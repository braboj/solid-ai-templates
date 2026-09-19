"""Read frozen efficacy trials for security, with checks declared after a run.

A run's pre-registered security checks can pass on every trial and separate
nothing. The checks here were declared in writing after such a run and before
any trial was read for them, so they can describe a run but never decide it:
the report prints them apart from the verdict vector.

Each trial is installed into a fresh environment of its own, because the
scoring environment holds the battery and the grader's requirements beside the
trial's. The static checks read the package roots the trial's score recorded.
A check that could not run is missing, never zero.
"""

import argparse
import ast
import datetime
import io
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lib  # noqa: E402
from harness import (LiveRunError, canonical, claim_area,  # noqa: E402
                     claim_refusal_check, release_area, remove_tree,
                     scoring_area, spellings)
from score import (absent, create_venv, lock_lines, measured, pip,  # noqa: E402
                   python_in, run, script_in)

SCRIPT = os.path.basename(__file__)
PACKAGE = "tariff"

# The auditor's version, pinned so a later reading of the same trial asks the
# same question. The vulnerability database it queries is not pinned, so the
# date of every audit is recorded beside its count.
PIP_AUDIT = "pip-audit==2.10.1"

SECRET_NAMES = ("SECRET_KEY", "WTF_CSRF_SECRET_KEY", "secret_key")
DEBUG_NAMES = ("DEBUG", "debug")
SQL_CALLS = ("execute", "executemany", "executescript")

# The calls whose keyword arguments set configuration by name.
KEYWORD_SETTERS = ("dict", "update", "from_mapping")

TEST_DIRECTORIES = ("tests", "test")


def source_files(roots):
    """Every Python file under the package roots, the trial's tests left out."""
    found = []
    for root in roots:
        if os.path.isfile(root):
            found.append(root)
            continue
        for base, directories, names in os.walk(root):
            directories[:] = [d for d in directories
                              if d not in TEST_DIRECTORIES
                              and d != "__pycache__"]
            found.extend(os.path.join(base, name) for name in sorted(names)
                         if name.endswith(".py")
                         and not name.startswith("test_"))
    return sorted(found)


def literal_string(node):
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def literal_true(node):
    return isinstance(node, ast.Constant) and node.value is True


def environment_lookup(func):
    """Whether a call reads the environment: `os.environ.get` or `getenv`."""
    if isinstance(func, ast.Name):
        return func.id == "getenv"
    if not isinstance(func, ast.Attribute):
        return False
    if func.attr == "getenv":
        return True
    owner = func.value
    return func.attr == "get" and (
        (isinstance(owner, ast.Attribute) and owner.attr == "environ")
        or (isinstance(owner, ast.Name) and owner.id == "environ"))


def supplies_literal(node):
    """Whether an expression hands over a string literal the environment
    did not supply: the literal itself, a lookup's default, or an `or`."""
    if literal_string(node):
        return True
    if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
        return any(literal_string(value) for value in node.values[1:])
    if isinstance(node, ast.Call) and environment_lookup(node.func):
        defaults = list(node.args[1:2]) + [keyword.value
                                           for keyword in node.keywords
                                           if keyword.arg == "default"]
        return any(literal_string(value) for value in defaults)
    return False


def target_name(target):
    """The configuration name an assignment target sets, or None."""
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    if isinstance(target, ast.Subscript) and literal_string(target.slice):
        return target.slice.value
    return None


def settings(tree):
    """Every (name, value node, line) the module assigns by name.

    Covers an assignment to a name, an attribute or a subscript key, and a
    keyword of `dict(...)`, `.update(...)` or `.from_mapping(...)`.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                name = target_name(target)
                if name:
                    yield name, node.value, node.lineno
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            name = target_name(node.target)
            if name:
                yield name, node.value, node.lineno
        elif isinstance(node, ast.Call):
            func = node.func
            called = (func.id if isinstance(func, ast.Name)
                      else func.attr if isinstance(func, ast.Attribute)
                      else None)
            if called in KEYWORD_SETTERS:
                for keyword in node.keywords:
                    if keyword.arg:
                        yield keyword.arg, keyword.value, node.lineno


def sql_built_from_strings(node):
    """Whether a statement argument is assembled rather than written out."""
    if isinstance(node, ast.JoinedStr):
        return any(isinstance(part, ast.FormattedValue)
                   for part in node.values)
    if isinstance(node, ast.BinOp):
        return isinstance(node.op, (ast.Mod, ast.Add))
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "format")


def static_findings(tree):
    """The three source checks' findings in one module, as line numbers."""
    found = {"secret_key": [], "debug": [], "sql_strings": []}
    for name, value, line in settings(tree):
        if name in SECRET_NAMES and supplies_literal(value):
            found["secret_key"].append(line)
        if name in DEBUG_NAMES and literal_true(value):
            found["debug"].append(line)
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)):
            continue
        if node.func.attr == "run" and any(
                keyword.arg == "debug" and literal_true(keyword.value)
                for keyword in node.keywords):
            found["debug"].append(node.lineno)
        if (node.func.attr in SQL_CALLS and node.args
                and sql_built_from_strings(node.args[0])):
            found["sql_strings"].append(node.lineno)
    return found


def static_checks(roots):
    """The hard-coded secret, debug and SQL checks over the package roots."""
    files = source_files(roots)
    if not files:
        reason = ("no source roots were recorded" if not roots
                  else "the source roots hold no Python file")
        return {key: absent(reason) for key in
                ("secret_key", "debug", "sql_strings")}
    locations = {"secret_key": [], "debug": [], "sql_strings": []}
    parsed, unparsed = 0, []
    for path in files:
        try:
            with io.open(path, encoding="utf-8", errors="replace") as handle:
                tree = ast.parse(handle.read(), filename=path)
        except (SyntaxError, ValueError):
            unparsed.append(path)
            continue
        parsed += 1
        for key, lines in static_findings(tree).items():
            locations[key].extend("%s:%d" % (path, line) for line in lines)
    if not parsed:
        return {key: absent("no source file parsed", unparsed=unparsed)
                for key in locations}
    return {key: measured(len(found), locations=found, files=parsed,
                          unparsed=unparsed)
            for key, found in locations.items()}


# Runs inside the trial's fresh environment, against the application the
# factory returns. Every request it sends is one the specification defines an
# answer to, so a stack trace in the response is the application's doing.
RUNTIME_SCRIPT = r'''
import json, os, re, sys, tempfile

report = {}
try:
    import tariff
    app = tariff.create_app(os.path.join(tempfile.mkdtemp(),
                                         "security-probe.sqlite"))
    client = app.test_client()
except Exception as error:
    print(json.dumps({"error": repr(error)[:300]}))
    raise SystemExit(0)

config = app.config
report["debug"] = bool(config.get("DEBUG"))
report["cookie_flags"] = {
    "httponly": bool(config.get("SESSION_COOKIE_HTTPONLY")),
    "samesite": str(config.get("SESSION_COOKIE_SAMESITE") or "").title()
    in ("Lax", "Strict"),
    "secure": bool(config.get("SESSION_COOKIE_SECURE")),
}

try:
    index = client.get("/")
    headers = index.headers
    policy = headers.get("Content-Security-Policy") or ""
    report["headers"] = {
        "content_security_policy": bool(policy),
        "nosniff": (headers.get("X-Content-Type-Options") or "").strip()
        .lower() == "nosniff",
        "framing": bool(headers.get("X-Frame-Options"))
        or "frame-ancestors" in policy.lower(),
        "referrer_policy": bool(headers.get("Referrer-Policy")),
    }
    report["index_status"] = index.status_code
except Exception as error:
    report["headers_error"] = repr(error)[:300]

LEAK = re.compile(r'Traceback \(most recent call last\)|__debugger__|'
                  r'Werkzeug Debugger|File "[^"]+", line \d+')


def hidden_fields(path):
    """The form's hidden inputs, which is where a CSRF token travels."""
    try:
        html = client.get(path).get_data(as_text=True)
    except Exception:
        return {}
    fields = {}
    for match in re.finditer(r'<input[^>]*type="hidden"[^>]*>', html,
                             re.IGNORECASE):
        name = re.search(r'name="([^"]+)"', match.group(0))
        value = re.search(r'value="([^"]*)"', match.group(0))
        if name:
            fields[name.group(1)] = value.group(1) if value else ""
    return fields


REQUESTS = (
    ("GET /invoices/not-a-number", "/invoices/not-a-number", None, None),
    ("GET /invoices/999999/export.json", "/invoices/999999/export.json",
     None, None),
    ("POST /invoices/preview quantity=abc", "/invoices/preview",
     "/invoices/new", {"jurisdiction": "DE", "currency": "EUR",
                       "sku": "WID-1", "quantity": "abc"}),
    ("POST /products unit_price=abc", "/products", "/products",
     {"sku": "SEC-1", "name": "Probe", "unit_price": "abc",
      "tax_category": "standard"}),
    ("POST /rules tiers={{{", "/rules", "/rules",
     {"rule_id": "sec-tier", "kind": "tiered", "sku": "", "tiers": "{{{"}),
)

outcomes = []
for label, path, form, body in REQUESTS:
    try:
        if body is None:
            response = client.get(path)
        else:
            data = dict(body)
            data.update(hidden_fields(form))
            response = client.post(path, data=data)
        text = response.get_data(as_text=True)
        outcomes.append({"request": label, "status": response.status_code,
                         "leaked": bool(LEAK.search(text))})
    except Exception as error:
        outcomes.append({"request": label, "status": None,
                         "raised": repr(error)[:200],
                         "leaked": report["debug"]})
report["error_requests"] = outcomes
print(json.dumps(report))
'''


def runtime_metrics(payload, reason=None):
    """The cookie, header and leakage metrics from the runtime probe's report.

    `reason` is why no report exists; every runtime metric carries it.
    """
    keys = ("cookie_flags", "security_headers", "error_leakage")
    if reason:
        return {key: absent(reason) for key in keys}
    if "error" in payload:
        return {key: absent("the application would not boot: %s"
                            % payload["error"]) for key in keys}
    flags = payload.get("cookie_flags") or {}
    metrics = {"cookie_flags": measured(sum(1 for on in flags.values() if on),
                                        flags=flags)}
    headers = payload.get("headers")
    if isinstance(headers, dict):
        metrics["security_headers"] = measured(
            sum(1 for on in headers.values() if on), present=headers,
            index_status=payload.get("index_status"))
    else:
        metrics["security_headers"] = absent(
            "`/` could not be requested: %s"
            % payload.get("headers_error", "no report"))
    requests = payload.get("error_requests")
    if isinstance(requests, list) and requests:
        metrics["error_leakage"] = measured(
            sum(1 for entry in requests if entry.get("leaked")),
            requests=requests, debug=payload.get("debug"))
    else:
        metrics["error_leakage"] = absent("no malformed request was sent")
    return metrics


def last_json(text):
    """The last line of a probe's output, parsed, or None."""
    try:
        return json.loads(text.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return None


def probe_runtime(venv, where):
    """Boot the installed application and read its cookies, headers, errors."""
    script = os.path.join(where, "runtime-probe.py")
    with io.open(script, "w", encoding="utf-8") as handle:
        handle.write(RUNTIME_SCRIPT)
    outcome = run([python_in(venv), script], cwd=where, timeout=600)
    payload = last_json(outcome["stdout"])
    if payload is None:
        return runtime_metrics({}, "the runtime probe produced no JSON: %s"
                               % (outcome["failed"] or outcome["stderr"]
                                  or outcome["stdout"])[-300:])
    return runtime_metrics(payload)


def audit_metric(report, audited_at):
    """Known vulnerabilities from `pip-audit`'s JSON report.

    An audit that checked no dependency answers zero for nothing scanned, so
    it is missing rather than clean.
    """
    try:
        payload = json.loads(report)
    except ValueError:
        return absent("pip-audit produced no JSON: %s" % report[:300])
    dependencies = payload.get("dependencies") if isinstance(
        payload, dict) else None
    if not isinstance(dependencies, list):
        return absent("pip-audit's report lists no dependencies")
    audited = [entry for entry in dependencies
               if isinstance(entry, dict) and not entry.get("skip_reason")]
    if not audited:
        return absent("pip-audit audited no dependency")
    vulnerable = [{"name": entry.get("name"), "version": entry.get("version"),
                   "ids": [vuln.get("id") for vuln in entry.get("vulns", [])]}
                  for entry in audited if entry.get("vulns")]
    return measured(sum(len(entry["ids"]) for entry in vulnerable),
                    audited=len(audited), vulnerable=vulnerable,
                    audited_at=audited_at)


def install_auditor(where):
    """The auditor's own environment, created once per scoring area."""
    binary = script_in(where, "pip-audit") if os.path.isdir(where) else None
    if binary:
        return binary, None
    venv = create_venv(where)
    outcome = pip(venv, "install", PIP_AUDIT)
    if outcome["failed"] or outcome["status"] != 0:
        return None, ("%s would not install: %s"
                      % (PIP_AUDIT, (outcome["stderr"]
                                     or outcome["stdout"])[-300:]))
    return script_in(venv, "pip-audit"), None


def audit_dependencies(venv, where, auditor):
    """Audit what the trial's own install put into its environment."""
    frozen = pip(venv, "freeze")
    if frozen["failed"] or frozen["status"] != 0:
        return absent("the environment could not be frozen: %s"
                      % (frozen["stderr"] or frozen["stdout"])[-300:])
    requirements = os.path.join(where, "freeze.txt")
    with io.open(requirements, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lock_lines(frozen["stdout"])) + "\n")
    audited_at = datetime.datetime.now().isoformat(timespec="seconds")
    outcome = run([auditor, "-r", requirements, "--no-deps", "--disable-pip",
                   "--format", "json", "--progress-spinner", "off"],
                  cwd=where, timeout=900)
    if outcome["failed"]:
        return absent("pip-audit %s" % outcome["failed"])
    return audit_metric(outcome["stdout"] or outcome["stderr"], audited_at)


def read_trial(area, name, scores_file, auditor, auditor_reason):
    """Every security check on one scored trial, read from its score file."""
    with io.open(scores_file, encoding="utf-8") as handle:
        scores = json.load(handle)
    roots = (scores.get("discovery") or {}).get("roots") or []
    tree = scores.get("workspace")

    result = {"name": name, "read_at": datetime.datetime.now().isoformat(
        timespec="seconds"), "auditor": PIP_AUDIT, "roots": roots}
    result.update(static_checks(roots))

    where = os.path.join(area, "security", name)
    os.makedirs(where, exist_ok=True)
    venv = create_venv(os.path.join(where, "venv"))
    installed = pip(venv, "install", tree, cwd=where)
    if installed["failed"] or installed["status"] != 0:
        reason = ("the trial did not install: %s"
                  % (installed["stderr"] or installed["stdout"])[-300:])
        result.update(runtime_metrics({}, reason))
        result["vulnerable_dependencies"] = absent(reason)
        return result

    result.update(probe_runtime(venv, where))
    if auditor is None:
        result["vulnerable_dependencies"] = absent(auditor_reason)
    else:
        result["vulnerable_dependencies"] = audit_dependencies(venv, where,
                                                               auditor)
    return result


# Plants for the self test: one module per check, written the way a trial
# would write it, each finding counted once.
EXPOSED_MODULE = '''import os

from flask import Flask

app = Flask(__name__)
SECRET_KEY = "dev"
app.config["SECRET_KEY"] = "literal"
app.secret_key = os.environ.get("SECRET_KEY", "fallback")
app.config.update(WTF_CSRF_SECRET_KEY="csrf")
app.config.from_mapping(SECRET_KEY=os.getenv("SECRET_KEY") or "late")
DEBUG = True
app.config["DEBUG"] = True
settings = dict(debug=True)


def main(conn, sku, rows, tail):
    conn.execute(f"SELECT * FROM products WHERE sku = '{sku}'")
    conn.execute("SELECT * FROM products WHERE sku = '%s'" % sku)
    conn.executemany("INSERT INTO {} VALUES (?)".format(tail), rows)
    conn.executescript("DROP TABLE " + tail)
    app.run(debug=True)
'''

HARDENED_MODULE = '''import os
import secrets

from flask import Flask

app = Flask(__name__)
SECRET_KEY = os.environ["SECRET_KEY"]
app.secret_key = secrets.token_hex(32)
app.config.update(SECRET_KEY=os.environ.get("SECRET_KEY"))
LABEL = "SECRET_KEY"
DEBUG = os.environ.get("FLASK_DEBUG") == "1"


def main(conn, sku):
    conn.execute("SELECT * FROM products WHERE sku = ?", (sku,))
    conn.execute(f"SELECT COUNT(*) FROM products")
    app.run(debug=False)
'''

# A stand-in application for the runtime probe, importable without Flask. It
# answers the probe's requests from a table, so each metric's reading is
# known before the probe runs.
FAKE_APP = '''import json

MODE = %(mode)r
TRACE = 'Traceback (most recent call last):\\n  File "app.py", line 9'


class Response(object):
    def __init__(self, status, body="", headers=None):
        self.status_code = status
        self.headers = headers or {}
        self._body = body

    def get_data(self, as_text=False):
        return self._body if as_text else self._body.encode("utf-8")


class Client(object):
    def get(self, path):
        if path == "/":
            if MODE == "hardened":
                return Response(200, "<p>home</p>", {
                    "Content-Security-Policy": "default-src 'self'; "
                                               "frame-ancestors 'none'",
                    "X-Content-Type-Options": "nosniff",
                    "Referrer-Policy": "same-origin"})
            return Response(200, "<p>home</p>")
        if path in ("/products", "/rules", "/invoices/new"):
            return Response(200, '<input type="hidden" name="csrf_token" '
                                 'value="t">')
        if MODE == "exposed" and path == "/invoices/not-a-number":
            return Response(500, TRACE)
        return Response(404, "not found")

    def post(self, path, data=None):
        if data.get("csrf_token") != "t":
            return Response(400, "missing token")
        if MODE == "exposed" and path == "/products":
            return Response(500, TRACE)
        if MODE == "exposed" and path == "/rules":
            raise ValueError("tiers")
        return Response(400, "invalid")


class App(object):
    def __init__(self):
        self.config = {"SESSION_COOKIE_HTTPONLY": True,
                       "DEBUG": MODE == "exposed"}
        if MODE == "hardened":
            self.config.update(SESSION_COOKIE_SAMESITE="lax",
                               SESSION_COOKIE_SECURE=True)

    def test_client(self):
        return Client()


def create_app(database):
    if MODE == "broken":
        raise RuntimeError("no factory today")
    return App()
'''

AUDIT_REPORT = json.dumps({"dependencies": [
    {"name": "flask", "version": "0.12", "vulns": [
        {"id": "PYSEC-2018-66"}, {"id": "PYSEC-2019-179"}]},
    {"name": "jinja2", "version": "3.1.6", "vulns": []},
    {"name": "tariff", "skip_reason": "not on PyPI"}], "fixes": []})


def static_self_checks(scratch):
    """The source checks count every planted form, and nothing else."""
    root = os.path.join(scratch, "static", "tariff")
    tests = os.path.join(root, "tests")
    os.makedirs(tests)
    for path, text in ((os.path.join(root, "exposed.py"), EXPOSED_MODULE),
                       (os.path.join(tests, "conftest.py"),
                        'SECRET_KEY = "test-only"\n'),
                       (os.path.join(root, "test_app.py"),
                        "DEBUG = True\n")):
        with io.open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
    exposed = static_checks([root])

    hardened_root = os.path.join(scratch, "static-hardened", "tariff")
    os.makedirs(hardened_root)
    with io.open(os.path.join(hardened_root, "app.py"), "w",
                 encoding="utf-8") as handle:
        handle.write(HARDENED_MODULE)
    hardened = static_checks([hardened_root])

    empty = os.path.join(scratch, "static-empty")
    os.makedirs(empty)
    return [
        ("every planted secret form is counted",
         exposed["secret_key"]["value"] == 5),
        ("every planted debug form is counted",
         exposed["debug"]["value"] == 4),
        ("every planted assembled statement is counted",
         exposed["sql_strings"]["value"] == 4),
        ("the trial's tests are not read", exposed["secret_key"]["files"] == 1),
        ("hardened source finds no secret",
         hardened["secret_key"]["value"] == 0),
        ("hardened source finds no debug", hardened["debug"]["value"] == 0),
        ("parameters and plain f-strings are not assembled SQL",
         hardened["sql_strings"]["value"] == 0),
        ("no roots is missing, not zero",
         all(metric["value"] is None and metric["missing"]
             for metric in static_checks([]).values())),
        ("roots holding no file are missing, not zero",
         all(metric["value"] is None and metric["missing"]
             for metric in static_checks([empty]).values())),
    ]


def runtime_self_checks(scratch):
    """The runtime probe reads each planted application as planted."""
    readings = {}
    for mode in ("hardened", "exposed", "broken"):
        where = os.path.join(scratch, "runtime-" + mode)
        package = os.path.join(where, "site", "tariff")
        os.makedirs(package)
        with io.open(os.path.join(package, "__init__.py"), "w",
                     encoding="utf-8") as handle:
            handle.write(FAKE_APP % {"mode": mode})
        script = os.path.join(where, "runtime-probe.py")
        with io.open(script, "w", encoding="utf-8") as handle:
            handle.write(RUNTIME_SCRIPT)
        env = dict(os.environ, PYTHONPATH=os.path.join(where, "site"))
        outcome = run([sys.executable, script], cwd=where, env=env,
                      timeout=120)
        payload = last_json(outcome["stdout"])
        readings[mode] = runtime_metrics(payload or {}, None if payload
                                         else "no JSON: %s"
                                         % outcome["stderr"][-200:])

    hardened, exposed = readings["hardened"], readings["exposed"]
    return [
        ("hardened cookies set all three flags",
         hardened["cookie_flags"]["value"] == 3),
        ("hardened headers are all four present",
         hardened["security_headers"]["value"] == 4),
        ("hardened errors leak nothing",
         hardened["error_leakage"]["value"] == 0),
        ("default cookies set one flag", exposed["cookie_flags"]["value"] == 1),
        ("absent headers count zero",
         exposed["security_headers"]["value"] == 0),
        ("two traces and a raise under debug are three leaks",
         exposed["error_leakage"]["value"] == 3),
        ("an app that will not boot is missing, not zero",
         all(metric["value"] is None and "would not boot" in metric["missing"]
             for metric in readings["broken"].values())),
    ]


def audit_self_checks():
    """The audit counts vulnerabilities, and an empty audit is missing."""
    counted = audit_metric(AUDIT_REPORT, "2026-09-16T00:00:00")
    skipped_only = audit_metric(json.dumps({"dependencies": [
        {"name": "tariff", "skip_reason": "not on PyPI"}]}), "now")
    return [
        ("every vulnerability of every package is counted",
         counted["value"] == 2 and counted["audited"] == 2),
        ("an audit of nothing is missing, not zero",
         skipped_only["value"] is None and skipped_only["missing"]),
        ("a report that is not JSON is missing",
         audit_metric("error: resolver", "now")["missing"] is not None),
    ]


def claim_self_checks(scratch):
    """A reading run refuses while another holds the area, and installs
    nothing.

    The planted build score gets the run past the refusal for a root with
    none, so the one it meets is the claim's.
    """
    root = os.path.join(scratch, "claimed")
    area = scoring_area(root)
    os.makedirs(os.path.join(area, "scores"))
    with io.open(os.path.join(area, "scores", "none-1.json"), "w",
                 encoding="utf-8") as handle:
        handle.write("{}")
    label, refused = claim_refusal_check(SCRIPT, main, root)
    return [(label, refused
             and not os.path.exists(os.path.join(area, "security")))]


def self_test():
    """Prove each check counts what it names, records missing as missing,
    and that a live run refuses a second."""
    scratch = os.path.join(tempfile.gettempdir(), "efficacy-security-self-test")
    remove_tree(scratch)
    os.makedirs(scratch)
    checks = (static_self_checks(scratch) + runtime_self_checks(scratch)
              + audit_self_checks() + claim_self_checks(scratch))
    for label, ok in checks:
        print("  %-52s %s" % (label, "ok" if ok else "FAILED"))
    remove_tree(scratch)
    passed = sum(1 for _, ok in checks if ok)
    lib.print_verdict(passed == len(checks),
                      "%d/%d self-test checks passed" % (passed, len(checks)))
    return 0 if passed == len(checks) else 1


def existing_file(directory, name):
    """The JSON file a trial's reading is filed under, in either spelling,
    or None."""
    for spelled in spellings(name):
        path = os.path.join(directory, "%s.json" % spelled)
        if os.path.isfile(path):
            return path
    return None


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Read scored efficacy trials for security.")
    parser.add_argument("--root", help="the harness's run root")
    parser.add_argument("--trial", action="append", default=[],
                        help="read only this trial, as none-1; repeatable")
    parser.add_argument("--reread", action="store_true",
                        help="read a trial already read; by default such a "
                             "trial is skipped")
    parser.add_argument("--self-test", action="store_true",
                        help="prove every check against planted trees; read "
                             "no trial")
    return parser.parse_args(argv)


def main(argv):
    options = parse_args(argv)
    if options.self_test:
        return self_test()
    if not options.root:
        print("--root is required unless --self-test is given")
        return 2

    # A score round 1 wrote sits under its letter name, `A1.json`, and is read
    # under its word, `none-1`.
    area = scoring_area(options.root)
    scores = os.path.join(area, "scores")
    scored = {canonical(os.path.splitext(entry)[0]):
              os.path.join(scores, entry)
              for entry in (sorted(os.listdir(scores))
                            if os.path.isdir(scores) else [])
              if entry.endswith(".json")}
    wanted = (sorted(canonical(name) for name in options.trial)
              if options.trial else sorted(scored))
    missing = [name for name in wanted if name not in scored]
    if not scored or missing:
        print("no build score for %s under %s; score.py writes them"
              % (", ".join(missing) or "any trial", area))
        return 2

    # A run clears each trial's environment before rebuilding it, so a second
    # run against the area deletes the one a live run is installing into.
    try:
        claim = claim_area(area, SCRIPT)
    except LiveRunError as error:
        print("refused: %s" % error)
        return 2
    try:
        return read_trials(options, area, scored, wanted)
    finally:
        release_area(claim)


def read_trials(options, area, scored, wanted):
    """Read each wanted trial not read yet; return the exit code."""
    # A trial already read keeps its reading, as a reused trial from an
    # earlier round does; the checks were declared after that round.
    target = os.path.join(area, "security-scores")
    done = []
    if not options.reread:
        for name in wanted:
            written = existing_file(target, name)
            if written:
                print("%s  already read at %s; --reread to read it again"
                      % (name, written))
                done.append(name)
        wanted = [name for name in wanted if name not in done]
    if not wanted:
        lib.print_verdict(True, "0 trial(s) read, %d already read"
                          % len(done))
        return 0

    auditor, reason = install_auditor(os.path.join(area, "security", "tools"))
    os.makedirs(target, exist_ok=True)
    for name in wanted:
        print("%s  reading" % name)
        result = read_trial(area, name, scored[name], auditor, reason)
        with io.open(os.path.join(target, "%s.json" % name), "w",
                     encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, sort_keys=True)
        print("  " + ", ".join(
            "%s %s" % (key, "missing" if result[key]["missing"]
                       else result[key]["value"])
            for key in ("secret_key", "debug", "sql_strings",
                        "vulnerable_dependencies", "cookie_flags",
                        "security_headers", "error_leakage")))
    lib.print_verdict(True, "%d trial(s) read, %d already read"
                      % (len(wanted), len(done)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
