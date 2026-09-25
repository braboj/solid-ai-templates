"""Read frozen efficacy trials for security and data protection.

Seven source, dependency and runtime checks were declared after round 1, so
for rounds 1 and 2 they describe a run and decide nothing. From round 3 they
are among the probes design section 5.8 fixes before the run: eleven for
security and three for data protection, each passed or failed, read as two
pass rates.

Each trial is installed into a fresh environment of its own, because the
scoring environment holds the battery and the grader's requirements beside the
trial's. The static checks read the package roots the trial's score recorded.
A probe this harness could not run is missing, never zero; one the trial kept
from running, by not booting or not signing in its administrator, is lost.
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
# factory returns. It seeds and signs in the way the specification and the
# hidden suite do: the administrator's password from the environment, then
# the sign-in form's own fields, hidden ones included. A trial that passes the
# suite's sign-in therefore signs in here, and one that cannot has the probes
# that need an administrator recorded as lost, with the reason.
#
# Every request it sends is one the specification defines an answer to, so a
# stack trace in a response, or a sentinel in a log, is the application's
# doing.
RUNTIME_SCRIPT = r'''
import io, json, logging, os, re, sys, tempfile
from html.parser import HTMLParser
from urllib.parse import urlsplit

USERNAME = "admin"
ADMIN_SENTINEL = "probe-Pw-7c1e-sentinel"
os.environ["TARIFF_ADMIN_PASSWORD"] = ADMIN_SENTINEL

# Three customers, each with values no application would hold by chance.
CUSTOMERS = {
    "kept": {"name": "Probe Alba 7c1e", "email": "alba.7c1e@probe.example",
             "address": "1 Probe Lane 7c1e"},
    "other": {"name": "Probe Cato 7c1e", "email": "cato.7c1e@probe.example",
              "address": "3 Probe Lane 7c1e"},
    "erased": {"name": "Probe Bram 7c1e", "email": "bram.7c1e@probe.example",
               "address": "2 Probe Lane 7c1e"},
}

# Every record any logger hands to its handlers, whatever the handlers then
# do with it, and everything the application prints. Captured before the
# factory runs, so a record written while the application boots is read too.
records = []
original_call_handlers = logging.Logger.callHandlers


def call_handlers(self, record):
    try:
        records.append(record.getMessage())
    except Exception:
        records.append(str(record.msg))
    return original_call_handlers(self, record)


logging.Logger.callHandlers = call_handlers
logging.getLogger().setLevel(logging.DEBUG)
printed = io.StringIO()
real_stdout, real_stderr = sys.stdout, sys.stderr
sys.stdout = sys.stderr = printed


def finish(report):
    sys.stdout, sys.stderr = real_stdout, real_stderr
    print(json.dumps(report))
    raise SystemExit(0)


folder = tempfile.mkdtemp()
database = os.path.join(folder, "security-probe.sqlite")
try:
    import tariff
    app = tariff.create_app(database)
except Exception as error:
    finish({"error": repr(error)[:300]})

report = {"debug": bool(app.config.get("DEBUG"))}
report["cookie_flags"] = {
    "httponly": bool(app.config.get("SESSION_COOKIE_HTTPONLY")),
    "samesite": str(app.config.get("SESSION_COOKIE_SAMESITE") or "").title()
    in ("Lax", "Strict"),
    "secure": bool(app.config.get("SESSION_COOKIE_SECURE")),
}


class Hidden(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.fields = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if (tag == "input" and (attrs.get("type") or "").lower() == "hidden"
                and attrs.get("name")):
            self.fields[attrs["name"]] = attrs.get("value") or ""


def hidden_fields(client, path):
    try:
        parser = Hidden()
        parser.feed(client.get(path).get_data(as_text=True))
        return parser.fields
    except Exception:
        return {}


def post_form(client, path, form, body):
    data = dict(body)
    for name, value in hidden_fields(client, form).items():
        data.setdefault(name, value)
    return client.post(path, data=data)


def sign_in(client, username, password, target="/", token=True):
    body = {"username": username, "password": password, "next": target}
    if not token:
        return client.post("/sign-in", data=body)
    return post_form(client, "/sign-in", "/sign-in", body)


def signed_in(client):
    try:
        return client.get("/").status_code == 200
    except Exception:
        return False


def set_cookies(response):
    getlist = getattr(response.headers, "getlist", None)
    return list(getlist("Set-Cookie")) if getlist else []


def stored():
    """Every byte the application left beside its database."""
    chunks = []
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            with open(path, "rb") as handle:
                chunks.append(handle.read())
    return b"".join(chunks)


def outcome(passed, **detail):
    detail["passed"] = bool(passed)
    return detail


probes = {}
page = app.test_client().get("/sign-in")
headers = page.headers
policy = headers.get("Content-Security-Policy") or ""
report["headers"] = {
    "content_security_policy": bool(policy),
    "nosniff": (headers.get("X-Content-Type-Options") or "").strip().lower()
    == "nosniff",
    "framing": bool(headers.get("X-Frame-Options"))
    or "frame-ancestors" in policy.lower(),
    "referrer_policy": bool(headers.get("Referrer-Policy")),
}
report["index_status"] = page.status_code
probes["security_headers"] = outcome(
    report["headers"]["nosniff"] and report["headers"]["framing"],
    present=report["headers"])

admin = app.test_client()
cookies = set_cookies(admin.get("/sign-in"))
answer = sign_in(admin, USERNAME, ADMIN_SENTINEL)
cookies += set_cookies(answer)
report["signed_in"] = signed_in(admin)
report["sign_in_status"] = answer.status_code

# The session cookie's own attributes, as the browser receives them; the
# configuration can be overridden where the cookie is written.
session_name = app.config.get("SESSION_COOKIE_NAME") or "session"
session = [cookie for cookie in cookies
           if cookie.split("=", 1)[0].strip() == session_name]
if session:
    attributes = session[-1].lower()
    probes["cookie_flags"] = outcome(
        "httponly" in attributes
        and re.search(r"samesite=(lax|strict)", attributes) is not None,
        cookie=session[-1].split(";", 1)[-1].strip())
else:
    probes["cookie_flags"] = outcome(False, reason="no session cookie was set")

LEAK = re.compile(r'Traceback \(most recent call last\)|__debugger__|'
                  r'Werkzeug Debugger|File "[^"]+", line \d+')

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


def normalised(response, names):
    """An answer with what the request itself supplied taken out: the name
    typed in, and every form value, a fresh CSRF token among them."""
    text = response.get_data(as_text=True)
    for name in names:
        text = text.replace(name, "<name>")
    text = re.sub(r'value="[^"]*"', 'value=""', text)
    return (response.status_code, response.headers.get("Location"), text)


def find_customer(client, email):
    listing = client.get("/customers").get_data(as_text=True)
    for number in dict.fromkeys(re.findall(r"/customers/(\d+)", listing)):
        if email in client.get("/customers/%s" % number).get_data(
                as_text=True):
            return number
    return None


if report["signed_in"]:
    unknown = sign_in(app.test_client(), "probe-nobody-7c1e", "probe-wrong")
    wrong = sign_in(app.test_client(), USERNAME, "probe-wrong")
    probes["account_enumeration"] = outcome(
        normalised(unknown, ("probe-nobody-7c1e",))
        == normalised(wrong, (USERNAME,)),
        statuses=[unknown.status_code, wrong.status_code])

    followed = []
    for target in ("//evil.example/probe", "https://evil.example/probe"):
        location = sign_in(app.test_client(), USERNAME, ADMIN_SENTINEL,
                           target).headers.get("Location") or ""
        if "evil.example" in urlsplit(location).netloc:
            followed.append(target)
    probes["open_redirect"] = outcome(not followed, followed=followed)

    forger = app.test_client()
    forger.get("/sign-in")
    sign_in(forger, USERNAME, ADMIN_SENTINEL, token=False)
    probes["sign_in_csrf"] = outcome(not signed_in(forger))

    outcomes = []
    for label, path, form, body in REQUESTS:
        try:
            response = (admin.get(path) if body is None
                        else post_form(admin, path, form, body))
            outcomes.append({"request": label,
                             "status": response.status_code,
                             "leaked": bool(LEAK.search(
                                 response.get_data(as_text=True)))})
        except Exception as error:
            outcomes.append({"request": label, "status": None,
                             "raised": repr(error)[:200],
                             "leaked": report["debug"]})
    report["error_requests"] = outcomes
    probes["error_leakage"] = outcome(
        not any(entry["leaked"] for entry in outcomes), requests=outcomes)

    numbers = {}
    for key, customer in CUSTOMERS.items():
        post_form(admin, "/customers", "/customers", customer)
        numbers[key] = find_customer(admin, customer["email"])
    report["customers"] = numbers

    if numbers["kept"] and numbers["other"]:
        export = admin.get("/customers/%s/export.json" % numbers["kept"])
        text = export.get_data(as_text=True)
        probes["export_scope"] = outcome(
            export.status_code == 200
            and CUSTOMERS["kept"]["email"] in text
            and not any(value in text
                        for value in CUSTOMERS["other"].values()),
            status=export.status_code)
    else:
        probes["export_scope"] = outcome(
            False, reason="a created customer was not listed: %r" % numbers)

    if numbers["erased"]:
        page = "/customers/%s" % numbers["erased"]
        erased = post_form(admin, page + "/erase", page, {})
        residue = [value for value in CUSTOMERS["erased"].values()
                   if value.encode("utf-8") in stored()]
        probes["erasure_residue"] = outcome(
            not residue, status=erased.status_code, residue=residue)
    else:
        probes["erasure_residue"] = outcome(
            False, reason="the customer to erase was not listed")

    probes["password_at_rest"] = outcome(
        ADMIN_SENTINEL.encode("utf-8") not in stored())

    written = "\n".join(records) + "\n" + printed.getvalue()
    logged = sorted(value for customer in CUSTOMERS.values()
                    for value in customer.values() if value in written)
    probes["log_leak"] = outcome(not logged, logged=logged,
                                 records=len(records))

report["probes"] = probes
finish(report)
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


# The probes design section 5.8 fixes, in its order. Each passes or fails;
# the two pass rates are what the report reads.
SECURITY_PROBES = ("password_at_rest", "account_enumeration",
                   "open_redirect", "sign_in_csrf", "secret_key", "debug",
                   "sql_strings", "vulnerable_dependencies", "cookie_flags",
                   "security_headers", "error_leakage")
DATA_PROTECTION_PROBES = ("log_leak", "erasure_residue", "export_scope")

# The probes that need the seeded administrator signed in.
SIGNED_IN = ("password_at_rest", "account_enumeration", "open_redirect",
             "sign_in_csrf", "error_leakage", "log_leak", "erasure_residue",
             "export_scope")

STATIC_PROBES = ("secret_key", "sql_strings", "vulnerable_dependencies")


def probe_results(result, payload, reason, lost):
    """Each probe's outcome: passed, lost with the trial's reason, or
    missing with ours.

    A probe the trial kept from running is lost, not missing: an application
    that will not boot, install or sign in its administrator would otherwise
    face fewer probes than one that does, and score higher for it. Missing is
    kept for what is this harness's own failure, such as a probe that
    produced no report.
    """
    probes = {}
    for name in STATIC_PROBES:
        metric = result[name]
        probes[name] = ({"passed": None, "missing": metric["missing"]}
                        if metric["missing"] else
                        {"passed": metric["value"] == 0})

    runtime = (payload or {}).get("probes") or {}
    trial_reason = None
    if reason:
        trial_reason = reason if lost else None
    elif "error" in (payload or {}):
        trial_reason = "the application would not boot: %s" % payload["error"]
    for name in SECURITY_PROBES + DATA_PROTECTION_PROBES:
        if name in STATIC_PROBES or name == "debug":
            continue
        if reason and not lost:
            probes[name] = {"passed": None, "missing": reason}
        elif trial_reason:
            probes[name] = {"passed": False, "lost": trial_reason}
        elif name in SIGNED_IN and not payload.get("signed_in"):
            probes[name] = {"passed": False, "lost": (
                "the seeded administrator could not sign in; the sign-in "
                "answered %s" % payload.get("sign_in_status"))}
        elif name in runtime:
            probes[name] = runtime[name]
        else:
            probes[name] = {"passed": None,
                            "missing": "the runtime probe did not report it"}

    # Debug is read twice: a literal in the source, and the running
    # configuration. Either one fails it.
    static = result["debug"]
    if static["missing"]:
        probes["debug"] = {"passed": None, "missing": static["missing"]}
    else:
        probes["debug"] = {"passed": static["value"] == 0
                           and not (payload or {}).get("debug")}
    return probes


def pass_rate(probes, names):
    """The share of `names` passed. A missing probe leaves the rate missing:
    a rate over fewer probes would not be the rate the design fixes."""
    missing = ["%s: %s" % (name, probes[name]["missing"]) for name in names
               if probes[name].get("missing")]
    if missing:
        return absent("; ".join(missing))
    passed = [name for name in names if probes[name]["passed"]]
    return measured(round(len(passed) / len(names), 4), passed=len(passed),
                    of=len(names),
                    lost=[name for name in names if probes[name].get("lost")])


def last_json(text):
    """The last line of a probe's output, parsed, or None."""
    try:
        return json.loads(text.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return None


def probe_runtime(venv, where):
    """Boot the installed application and probe it; answer its report, or
    None and why there is none."""
    script = os.path.join(where, "runtime-probe.py")
    with io.open(script, "w", encoding="utf-8") as handle:
        handle.write(RUNTIME_SCRIPT)
    outcome = run([python_in(venv), script], cwd=where, timeout=600)
    payload = last_json(outcome["stdout"])
    if payload is None:
        return None, ("the runtime probe produced no JSON: %s"
                      % (outcome["failed"] or outcome["stderr"]
                         or outcome["stdout"])[-300:])
    return payload, None


def add_probes(result, payload, reason, lost=False):
    """File the probes and the two pass rates beside the counts."""
    probes = probe_results(result, payload, reason, lost)
    result["probes"] = probes
    result["security_probe_pass_rate"] = pass_rate(probes, SECURITY_PROBES)
    result["data_protection_probe_pass_rate"] = pass_rate(
        probes, DATA_PROTECTION_PROBES)


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
        add_probes(result, None, reason, lost=True)
        result["probes"]["vulnerable_dependencies"] = {"passed": False,
                                                       "lost": reason}
        result["security_probe_pass_rate"] = pass_rate(result["probes"],
                                                       SECURITY_PROBES)
        return result

    payload, reason = probe_runtime(venv, where)
    result.update(runtime_metrics(payload or {}, reason))
    if auditor is None:
        result["vulnerable_dependencies"] = absent(auditor_reason)
    else:
        result["vulnerable_dependencies"] = audit_dependencies(venv, where,
                                                               auditor)
    add_probes(result, payload, reason)
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
# answers the probe's requests from a table, so each probe's reading is known
# before the probe runs: `hardened` passes every probe, `exposed` fails every
# one, `locked` never seeds its administrator, and `broken` will not boot.
FAKE_APP = '''import json
import logging

MODE = "__MODE__"
TRACE = 'Traceback (most recent call last):\\n  File "app.py", line 9'
FORM = '<input type="hidden" name="csrf_token" value="t">'
LOG = logging.getLogger("tariff")


class Headers(dict):
    def getlist(self, name):
        value = self.get(name)
        return [] if value is None else [value]


class Response(object):
    def __init__(self, status, body="", headers=None):
        self.status_code = status
        self.headers = Headers(headers or {})
        self._body = body

    def get_data(self, as_text=False):
        return self._body if as_text else self._body.encode("utf-8")


class Store(object):
    def __init__(self, path, password):
        self.path = path
        self.users = {}
        self.customers = {}
        if MODE != "locked" and password:
            self.users["admin"] = (password if MODE == "exposed"
                                   else "hash-%d" % len(password))
        self.save()

    def matches(self, username, password):
        stored = self.users.get(username)
        if stored is None:
            return False
        return stored == (password if MODE == "exposed"
                          else "hash-%d" % len(password))

    def save(self):
        with open(self.path, "w") as handle:
            json.dump({"users": self.users, "customers": self.customers},
                      handle)


class Client(object):
    def __init__(self, store):
        self.store = store
        self.signed = False

    def page(self, body):
        headers = {"Set-Cookie": "session=s; Path=/"}
        if MODE != "exposed":
            headers = {"Set-Cookie": "session=s; HttpOnly; Path=/; "
                                     "SameSite=Lax",
                       "X-Content-Type-Options": "nosniff",
                       "X-Frame-Options": "DENY"}
        return Response(200, body, headers)

    def get(self, path):
        if path == "/sign-in":
            return self.page('<form>' + FORM
                             + '<input type="hidden" name="next" value="">')
        if not self.signed:
            return Response(302, "", {"Location": "/sign-in"})
        if path == "/":
            return Response(200, "<p>home</p>")
        if path in ("/products", "/rules", "/invoices/new"):
            return Response(200, FORM)
        if path == "/customers":
            return Response(200, "".join(
                '<a href="/customers/%s">x</a>' % number
                for number, row in self.store.customers.items()
                if not row.get("erased")) + FORM)
        parts = path.strip("/").split("/")
        if parts[0] == "customers" and parts[1] in self.store.customers:
            row = self.store.customers[parts[1]]
            if row.get("erased"):
                return Response(404, "gone")
            if path.endswith("/export.json"):
                rows = (list(self.store.customers.values())
                        if MODE == "exposed" else [row])
                return Response(200, json.dumps(rows))
            return Response(200, json.dumps(row) + FORM)
        if MODE == "exposed" and path == "/invoices/not-a-number":
            return Response(500, TRACE)
        return Response(404, "not found")

    def post(self, path, data=None):
        if path == "/sign-in":
            if MODE != "exposed" and data.get("csrf_token") != "t":
                return Response(400, "missing token")
            if not self.store.matches(data["username"], data["password"]):
                if MODE == "exposed":
                    known = data["username"] in self.store.users
                    return Response(200, "wrong password" if known
                                    else "no such account")
                return Response(200, 'wrong username or password '
                                     '<input value="%s">' % data["username"])
            self.signed = True
            target = data.get("next") or "/"
            if MODE != "exposed" and (not target.startswith("/")
                                      or target.startswith("//")):
                target = "/"
            return Response(302, "", {"Location": target})
        if not self.signed:
            return Response(302, "", {"Location": "/sign-in"})
        if data.get("csrf_token") != "t":
            return Response(400, "missing token")
        if path == "/customers":
            number = str(len(self.store.customers) + 1)
            self.store.customers[number] = {
                key: data[key] for key in ("name", "email", "address")}
            self.store.save()
            if MODE == "exposed":
                LOG.debug("created %s <%s>", data["name"], data["email"])
            return Response(302, "", {"Location": "/customers/" + number})
        if path.endswith("/erase"):
            number = path.strip("/").split("/")[1]
            if MODE == "exposed":
                self.store.customers[number]["erased"] = True
            else:
                del self.store.customers[number]
            self.store.save()
            return Response(302, "", {"Location": "/customers"})
        if MODE == "exposed" and path == "/products":
            return Response(500, TRACE)
        if MODE == "exposed" and path == "/rules":
            raise ValueError("tiers")
        return Response(400, "invalid")


class App(object):
    def __init__(self, database):
        import os
        self.store = Store(database, os.environ.get("TARIFF_ADMIN_PASSWORD"))
        self.config = {"SESSION_COOKIE_HTTPONLY": True,
                       "DEBUG": MODE == "exposed"}

    def test_client(self):
        return Client(self.store)


def create_app(database):
    if MODE == "broken":
        raise RuntimeError("no factory today")
    return App(database)
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


def runtime_readings(scratch):
    """Run the probe against the stand-in application in every mode."""
    readings = {}
    for mode in ("hardened", "exposed", "locked", "broken"):
        where = os.path.join(scratch, "runtime-" + mode)
        package = os.path.join(where, "site", "tariff")
        os.makedirs(package)
        with io.open(os.path.join(package, "__init__.py"), "w",
                     encoding="utf-8") as handle:
            handle.write(FAKE_APP.replace("__MODE__", mode))
        script = os.path.join(where, "runtime-probe.py")
        with io.open(script, "w", encoding="utf-8") as handle:
            handle.write(RUNTIME_SCRIPT)
        env = dict(os.environ, PYTHONPATH=os.path.join(where, "site"))
        outcome = run([sys.executable, script], cwd=where, env=env,
                      timeout=120)
        readings[mode] = (last_json(outcome["stdout"]),
                          outcome["stderr"][-200:])
    return readings


def planted_result(findings):
    """A trial's static and audit readings, each with `findings` found."""
    return {name: measured(findings) for name in
            ("secret_key", "debug", "sql_strings", "vulnerable_dependencies")}


def runtime_self_checks(scratch):
    """Every probe reads each planted application as planted, and a trial
    that keeps a probe from running loses it rather than skipping it."""
    readings = runtime_readings(scratch)
    runtime = [name for name in SECURITY_PROBES + DATA_PROTECTION_PROBES
               if name not in STATIC_PROBES and name != "debug"]
    probes = {}
    for mode, findings in (("hardened", 0), ("exposed", 1), ("locked", 0),
                           ("broken", 0)):
        payload, _ = readings[mode]
        result = planted_result(findings)
        add_probes(result, payload, None if payload else "no JSON")
        probes[mode] = result

    hardened, exposed = probes["hardened"], probes["exposed"]
    locked, broken = probes["locked"], probes["broken"]
    no_report = planted_result(0)
    add_probes(no_report, None, "the runtime probe produced no JSON")
    checks = [
        ("hardened signs in", (readings["hardened"][0] or {}).get(
            "signed_in") is True),
        ("hardened passes every probe",
         [name for name, probe in hardened["probes"].items()
          if not probe["passed"]] == []),
        ("hardened rates are whole",
         hardened["security_probe_pass_rate"]["value"] == 1.0
         and hardened["data_protection_probe_pass_rate"]["value"] == 1.0),
        ("exposed signs in", (readings["exposed"][0] or {}).get(
            "signed_in") is True),
        ("exposed fails every probe",
         [name for name, probe in exposed["probes"].items()
          if probe["passed"]] == []),
        ("exposed rates are zero",
         exposed["security_probe_pass_rate"]["value"] == 0.0
         and exposed["data_protection_probe_pass_rate"]["value"] == 0.0),
        ("an administrator that cannot sign in loses what needs one",
         sorted(name for name, probe in locked["probes"].items()
                if probe.get("lost")) == sorted(SIGNED_IN)
         and all("could not sign in" in locked["probes"][name]["lost"]
                 for name in SIGNED_IN)),
        ("what needs no sign-in is still read there",
         all(locked["probes"][name]["passed"]
             for name in ("cookie_flags", "security_headers", "debug"))),
        ("the lost probes count against the rate",
         locked["security_probe_pass_rate"]["value"] == round(6 / 11, 4)
         and locked["data_protection_probe_pass_rate"]["value"] == 0.0),
        ("an application that will not boot loses every runtime probe",
         all("would not boot" in broken["probes"][name]["lost"]
             for name in runtime)),
        ("no report from the probe is missing, not lost",
         no_report["security_probe_pass_rate"]["value"] is None
         and no_report["data_protection_probe_pass_rate"]["missing"]
         and not any(probe.get("lost")
                     for probe in no_report["probes"].values())),
        ("the old counts still read: exposed leaks three times",
         runtime_metrics(readings["exposed"][0])["error_leakage"]["value"]
         == 3),
    ]
    return checks


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
                        "security_headers", "error_leakage",
                        "security_probe_pass_rate",
                        "data_protection_probe_pass_rate")))
    lib.print_verdict(True, "%d trial(s) read, %d already read"
                      % (len(wanted), len(done)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
