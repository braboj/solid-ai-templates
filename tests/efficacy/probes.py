"""Structural and web-quality probes for one frozen efficacy trial.

`score.py` owns the backbone — install, hidden suite, static battery, scope
and cost — and calls in here for the two families of measurement that need to
reach inside the trial's own interpreter: the structural design probes of the
design's section 5, and the web-quality probes beside them.

Both run as one script inside the trial's environment, because `grimp`, the
application factory and the browser all live there. A probe that cannot run
returns a missing metric naming what was absent; it never returns zero.
"""

import io
import json
import os

# The package and the factory the specification fixes. Everything in here
# reaches the trial only through those two names and the routes, never through
# a module path the arm was free to choose.
PACKAGE = "tariff"

# The section 5 surface. A name missing from a trial is a finding; a name the
# trial adds is reported as extra rather than as wrong.
REQUIRED_NAMES = ("Product", "Catalog", "InvoiceLine", "Invoice",
                  "Jurisdiction", "PercentageRule", "BulkRule", "TieredRule",
                  "CouponRule", "price", "TariffError")


class Context(object):
    """What a probe needs from the scorer, passed rather than imported.

    `score.py` already owns the command runner and the missing-vs-zero
    constructors, and importing them back from here would make the two
    modules circular.
    """

    def __init__(self, run, measured, absent, python, script):
        self.run = run
        self.measured = measured
        self.absent = absent
        self.python = python
        self.script = script


# Runs inside the trial's environment and prints one JSON object. Kept as a
# script rather than an import because the interpreter that must answer is the
# trial's, not the scorer's.
STRUCTURE_SCRIPT = r'''
import ast, json, os, sys

PACKAGE = "tariff"
REQUIRED = %(required)r
ROOTS = json.loads(sys.argv[1])

report = {}


def source_files(roots):
    found = []
    for root in roots:
        if os.path.isfile(root) and root.endswith(".py"):
            found.append(root)
            continue
        for base, _, names in os.walk(root):
            if "__pycache__" in base:
                continue
            for name in names:
                if name.endswith(".py"):
                    found.append(os.path.join(base, name))
    return found


FILES = source_files(ROOTS)
TREES = {}
for path in FILES:
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            TREES[path] = ast.parse(handle.read(), filename=path)
    except SyntaxError as error:
        report.setdefault("unparsed", []).append([path, str(error)])


def imported_names(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


# Role assignment by what a module imports, because the arms name their
# modules freely. A module that imports flask is web; one that imports a
# database driver is persistence; the rest is domain, which is what the
# layering contract is about.
WEB = {"flask", "werkzeug", "jinja2"}
STORE = {"sqlite3", "sqlalchemy"}
roles = {}
for path, tree in TREES.items():
    imports = imported_names(tree)
    if imports & WEB:
        roles[path] = "web"
    elif imports & STORE:
        roles[path] = "persistence"
    else:
        roles[path] = "domain"
report["roles"] = {os.path.basename(p): r for p, r in roles.items()}

# The contract the specification states in its own words: `import tariff`
# works without Flask and without touching the database, so no domain module
# may reach either.
violations = []
for path, tree in TREES.items():
    if roles[path] != "domain":
        continue
    for name in sorted(imported_names(tree) & (WEB | STORE)):
        violations.append([os.path.basename(path), name])
report["layering_violations"] = violations


def is_route(node):
    for decorator in getattr(node, "decorator_list", []):
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        attribute = getattr(target, "attr", None)
        if attribute in ("route", "get", "post", "put", "delete"):
            return True
    return False


# Pricing arithmetic inside a route is the concrete form of the layering
# question: a route that multiplies Decimals is doing the domain's work.
money_in_routes = []
for path, tree in TREES.items():
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not is_route(node):
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.BinOp) and isinstance(
                    inner.op, (ast.Mult, ast.Div, ast.Sub, ast.Add)):
                segment = ast.dump(inner)
                if "Decimal" in segment or "unit_price" in segment:
                    money_in_routes.append([os.path.basename(path), node.name])
                    break
report["money_in_routes"] = money_in_routes

# A boolean parameter is a branch the caller cannot name, which `oop.md`
# treats as a smell rather than a style preference.
bool_parameters = []
for path, tree in TREES.items():
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        arguments = list(node.args.args) + list(node.args.kwonlyargs)
        for argument in arguments:
            annotation = getattr(argument, "annotation", None)
            if isinstance(annotation, ast.Name) and annotation.id == "bool":
                bool_parameters.append(
                    [os.path.basename(path), node.name, argument.arg])
        for default in list(node.args.defaults) + list(
                node.args.kw_defaults or []):
            if isinstance(default, ast.Constant) and isinstance(
                    default.value, bool):
                bool_parameters.append(
                    [os.path.basename(path), node.name, "default"])
report["bool_parameters"] = bool_parameters


# The extension axes the change task will exercise. Each is scored present or
# absent on the property, not on a pattern's name: an abstract base, a typed
# protocol or a registry all answer "a new kind needs no edit to an existing
# one".
def has_abstraction(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                label = getattr(base, "id", getattr(base, "attr", ""))
                if label in ("Protocol", "ABC"):
                    return True
            for decorator in node.decorator_list:
                if getattr(decorator, "id", "") == "runtime_checkable":
                    return True
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                target = (decorator.func if isinstance(decorator, ast.Call)
                          else decorator)
                if getattr(target, "attr", "") in ("register", "registry"):
                    return True
    return False


def mentions(tree, words):
    dumped = ast.dump(tree)
    return any(word in dumped for word in words)


axes = {}
for label, words in (("rule_kinds", ["Rule", "rule_kind", "KINDS"]),
                     ("jurisdictions", ["Jurisdiction", "rates"]),
                     ("export_formats", ["export", "Export", "csv", "json"])):
    present = False
    for path, tree in TREES.items():
        if mentions(tree, words) and has_abstraction(tree):
            present = True
            break
    axes[label] = present
report["extension_points"] = axes

# A conditional ladder over rule kinds is the missed-Strategy signal the judge
# is asked to score; counting the widest one here gives it a number to quote.
ladders = []
for path, tree in TREES.items():
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            depth, cursor = 1, node
            while cursor.orelse and len(cursor.orelse) == 1 and isinstance(
                    cursor.orelse[0], ast.If):
                cursor = cursor.orelse[0]
                depth += 1
            if depth >= 3 and mentions(node, ["kind", "Rule", "percent"]):
                ladders.append([os.path.basename(path), depth])
report["kind_ladders"] = ladders

# Public surface, against what section 5 requires.
try:
    import importlib
    module = importlib.import_module(PACKAGE)
    exported = list(getattr(module, "__all__", []) or
                    [n for n in dir(module) if not n.startswith("_")])
    report["surface"] = {
        "missing": [n for n in REQUIRED if not hasattr(module, n)],
        "extra": [n for n in exported if n not in REQUIRED],
        "exported": len(exported),
    }
except Exception as error:
    report["surface"] = {"error": repr(error)[:300]}

# IO isolation: `price` takes values, so no parameter of it may be annotated
# as a connection, a cursor, a row or a request.
try:
    import inspect
    import importlib
    module = importlib.import_module(PACKAGE)
    price = getattr(module, "price", None)
    if price is None:
        report["io_isolation"] = {"error": "no price function is exported"}
    else:
        signature = inspect.signature(price)
        leaked = [name for name, parameter in signature.parameters.items()
                  if any(token in str(parameter.annotation).lower()
                         for token in ("connection", "cursor", "row",
                                       "request", "session", "engine"))]
        report["io_isolation"] = {
            "parameters": list(signature.parameters),
            "leaked": leaked,
            "clean": not leaked,
        }
except Exception as error:
    report["io_isolation"] = {"error": repr(error)[:300]}

# Cycles, fan-in and fan-out, from the import graph rather than from names.
try:
    import grimp
    graph = grimp.build_graph(PACKAGE)
    modules = sorted(graph.modules)
    cycles = 0
    instability = {}
    for name in modules:
        outward = len(graph.find_modules_directly_imported_by(name))
        inward = len(graph.find_modules_that_directly_import(name))
        total = outward + inward
        instability[name] = round(outward / total, 3) if total else None
    for name in modules:
        for other in graph.find_modules_directly_imported_by(name):
            if name in graph.find_modules_directly_imported_by(other):
                cycles += 1
    domain = [v for k, v in instability.items()
              if v is not None and "web" not in k and "app" not in k]
    report["graph"] = {
        "modules": len(modules),
        "mutual_import_pairs": cycles // 2,
        "mean_instability": (round(sum(domain) / len(domain), 3)
                             if domain else None),
    }
except Exception as error:
    report["graph"] = {"error": repr(error)[:300]}

# The four facts the adherence checklist needs and no tool reports: what the
# library writes to the host's streams, whether a comment cites a ticket
# number, and whether one error hierarchy covers every raised type.
prints, citations, raises, bases = [], [], [], []
for path, tree in TREES.items():
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(
                node.func, "id", "") == "print":
            prints.append([os.path.basename(path), node.lineno])
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                label = getattr(base, "id", getattr(base, "attr", ""))
                if label in ("Exception", "BaseException", "ValueError",
                             "TypeError", "RuntimeError"):
                    bases.append([os.path.basename(path), node.name, label])
report["print_calls"] = prints
report["exception_bases"] = bases

CITATION = None
try:
    import re as _re
    CITATION = _re.compile(r"#\s?\d{2,}|ADR-\d+|PR\s?#\d+")
except Exception:
    CITATION = None
if CITATION is not None:
    for path in FILES:
        try:
            with open(path, encoding="utf-8", errors="replace") as handle:
                for number, line in enumerate(handle, 1):
                    stripped = line.strip()
                    if stripped.startswith("#") and CITATION.search(stripped):
                        citations.append([os.path.basename(path), number])
        except OSError:
            continue
report["citations"] = citations

# A library writes nothing to the host's streams: where logging is used at
# all, a NullHandler is what makes that true. Where it is not used the
# question does not arise, which is a third answer and not a pass.
uses_logging, null_handler = False, False
for path, tree in TREES.items():
    if "logging" in imported_names(tree):
        uses_logging = True
    if "NullHandler" in ast.dump(tree):
        null_handler = True
report["logging"] = {"used": uses_logging, "null_handler": null_handler}

report["files_parsed"] = len(TREES)
print(json.dumps(report))
'''


# Runs inside the trial's environment against the application the factory
# returns. Every probe here is one the specification already fixes: the
# routes, the CSRF refusal, the escaping of what a form stored.
WEB_SCRIPT = r'''
import json, os, re, sys, tempfile

PACKAGE = "tariff"
report = {}

try:
    import importlib
    package = importlib.import_module(PACKAGE)
    database = os.path.join(tempfile.mkdtemp(), "web-probe.sqlite")
    app = package.create_app(database)
    app.config["WTF_CSRF_ENABLED"] = app.config.get("WTF_CSRF_ENABLED", True)
    client = app.test_client()
except Exception as error:
    print(json.dumps({"error": repr(error)[:300]}))
    raise SystemExit(0)


def hidden_fields(html):
    """Every hidden input in the page, which is where a CSRF token hides.

    The field's name is the arm's choice -- the specification fixes the
    visible fields and leaves the rest -- so the probe carries whatever the
    form carries rather than guessing a name.
    """
    fields = {}
    for match in re.finditer(r'<input[^>]*type="hidden"[^>]*>', html,
                             re.IGNORECASE):
        tag = match.group(0)
        name = re.search(r'name="([^"]+)"', tag)
        value = re.search(r'value="([^"]*)"', tag)
        if name:
            fields[name.group(1)] = value.group(1) if value else ""
    return fields


PAYLOAD = "<script>alert(1)</script>"

try:
    page = client.get("/products")
    html = page.get_data(as_text=True)
    token = hidden_fields(html)
    report["products_status"] = page.status_code

    # CSRF: the same body without the hidden fields must be refused, and the
    # specification names the statuses.
    bare = client.post("/products", data={"sku": "XSS-1", "name": PAYLOAD,
                                          "unit_price": "1.00",
                                          "tax_category": "standard"})
    report["csrf_refused_without_token"] = bare.status_code in (400, 403)
    report["csrf_status"] = bare.status_code

    body = {"sku": "XSS-1", "name": PAYLOAD, "unit_price": "1.00",
            "tax_category": "standard"}
    body.update(token)
    created = client.post("/products", data=body, follow_redirects=True)
    report["create_status"] = created.status_code

    # The payload must come back inert on every page that can show a product
    # name. A page that renders it raw is the finding, not the one that
    # escapes it.
    raw_pages = []
    for path in ("/products", "/invoices/new"):
        shown = client.get(path).get_data(as_text=True)
        if PAYLOAD in shown:
            raw_pages.append(path)
    report["xss_raw_pages"] = raw_pages
    report["xss_inert"] = not raw_pages
except Exception as error:
    report["form_probe_error"] = repr(error)[:300]

try:
    builder = client.get("/invoices/new")
    html = builder.get_data(as_text=True)
    report["builder_bytes"] = len(builder.get_data())

    # Subresources the builder asks the browser to fetch. The specification
    # allows one vendored script and no bundler, so this is a number with a
    # stated expectation rather than a bare count.
    requests = re.findall(r'(?:src|href)="(?!http|//|#|mailto)([^"]+)"', html)
    assets = [r for r in requests if not r.endswith("/")
              and "." in os.path.basename(r)]
    report["builder_subrequests"] = len(assets)
    report["builder_assets"] = assets[:20]
    report["builder_status"] = builder.status_code
except Exception as error:
    report["builder_probe_error"] = repr(error)[:300]

# Saved HTML for the validator, which runs outside this interpreter.
try:
    target = sys.argv[1]
    os.makedirs(target, exist_ok=True)
    for label, path in (("index", "/"), ("products", "/products"),
                        ("rules", "/rules"),
                        ("jurisdictions", "/jurisdictions"),
                        ("builder", "/invoices/new")):
        response = client.get(path)
        with open(os.path.join(target, label + ".html"), "wb") as handle:
            handle.write(response.get_data())
    report["saved_pages"] = True
except Exception as error:
    report["saved_pages"] = False
    report["save_error"] = repr(error)[:300]

print(json.dumps(report))
'''


def structure(ctx, workspace, roots, seen):
    """The structural design measures, as one probe inside the trial's venv."""
    if not roots:
        return ctx.absent("no source roots were discovered", seen=seen)
    script = os.path.join(workspace, ".score-structure.py")
    with io.open(script, "w", encoding="utf-8") as handle:
        handle.write(STRUCTURE_SCRIPT % {"required": list(REQUIRED_NAMES)})
    outcome = ctx.run([ctx.python, script, json.dumps(roots)], cwd=workspace)
    if outcome["failed"]:
        return ctx.absent("the structure probe %s" % outcome["failed"],
                          seen=seen, invocation=outcome["argv"])
    try:
        payload = json.loads(outcome["stdout"].strip().splitlines()[-1])
    except (ValueError, IndexError):
        return ctx.absent("the structure probe produced no JSON: %s"
                          % (outcome["stderr"] or outcome["stdout"])[:300],
                          seen=seen, invocation=outcome["argv"])
    if not payload.get("files_parsed"):
        return ctx.absent("the structure probe parsed no files", seen=seen,
                          invocation=outcome["argv"])
    return ctx.measured(payload, seen=seen, invocation=outcome["argv"])


def html_validity(ctx, pages):
    """HTML validity over the pages the web probe saved.

    The validator needs a Java runtime. Where the machine has none the metric
    is missing and says so, which is the difference between valid HTML and
    unchecked HTML.
    """
    binary = ctx.script("html5validator")
    if binary is None:
        return ctx.absent("html5validator is not installed")
    if not os.path.isdir(pages):
        return ctx.absent("the web probe saved no pages to validate")
    outcome = ctx.run([binary, "--root", pages, "--format", "json"],
                      cwd=pages)
    if outcome["failed"]:
        return ctx.absent("html5validator %s" % outcome["failed"])
    text = outcome["stdout"] + outcome["stderr"]
    if "java" in text.lower() and "not" in text.lower() and not \
            outcome["stdout"].strip():
        return ctx.absent("no Java runtime, so validity was not checked")
    try:
        findings = json.loads(outcome["stdout"] or "[]")
    except ValueError:
        # The validator prints one message per line when it is not given a
        # parseable format; counting those lines is still a measurement, and
        # an empty output with a zero status is a clean run.
        lines = [line for line in text.splitlines() if ".html" in line]
        if not lines and outcome["status"] == 0:
            return ctx.measured(0)
        return ctx.measured(len(lines), raw=lines[:20])
    errors = [f for f in findings if f.get("type") == "error"]
    return ctx.measured(len(errors), total=len(findings))


def accessibility(ctx, workspace, pages):
    """axe-core violations at WCAG 2.1 AA, over the saved pages.

    Needs a browser binary. Absent one, the row is missing rather than clean:
    an accessibility score nobody measured is not a passing score.
    """
    if not os.path.isdir(pages):
        return ctx.absent("the web probe saved no pages to scan")
    script = os.path.join(workspace, ".score-axe.py")
    body = (
        "import glob, json, os, sys\n"
        "try:\n"
        "    from playwright.sync_api import sync_playwright\n"
        "    from axe_playwright_python.sync_playwright import Axe\n"
        "except Exception as error:\n"
        "    print(json.dumps({'error': repr(error)[:200]}))\n"
        "    raise SystemExit(0)\n"
        "results = {}\n"
        "try:\n"
        "    with sync_playwright() as playwright:\n"
        "        browser = playwright.chromium.launch()\n"
        "        page = browser.new_page()\n"
        "        axe = Axe()\n"
        "        for path in sorted(glob.glob(os.path.join(sys.argv[1],\n"
        "                                                  '*.html'))):\n"
        "            page.goto('file://' + os.path.abspath(path))\n"
        "            report = axe.run(page)\n"
        "            results[os.path.basename(path)] = report.violations_count\n"
        "        browser.close()\n"
        "except Exception as error:\n"
        "    print(json.dumps({'error': repr(error)[:200]}))\n"
        "    raise SystemExit(0)\n"
        "print(json.dumps({'violations': results}))\n")
    with io.open(script, "w", encoding="utf-8") as handle:
        handle.write(body)
    outcome = ctx.run([ctx.python, script, pages], cwd=workspace)
    try:
        payload = json.loads(outcome["stdout"].strip().splitlines()[-1])
    except (ValueError, IndexError):
        return ctx.absent("the accessibility probe produced no JSON: %s"
                          % (outcome["stderr"] or outcome["stdout"])[:200])
    if "error" in payload:
        return ctx.absent("axe could not run: %s" % payload["error"])
    counts = payload.get("violations", {})
    if not counts:
        return ctx.absent("axe scanned no pages")
    return ctx.measured(sum(counts.values()), per_page=counts)


def web_quality(ctx, workspace):
    """The web-quality family: escaping, CSRF, weight, validity, axe."""
    pages = os.path.join(workspace, ".score-pages")
    script = os.path.join(workspace, ".score-web.py")
    with io.open(script, "w", encoding="utf-8") as handle:
        handle.write(WEB_SCRIPT)
    outcome = ctx.run([ctx.python, script, pages], cwd=workspace)
    if outcome["failed"]:
        return ctx.absent("the web probe %s" % outcome["failed"],
                          invocation=outcome["argv"])
    try:
        payload = json.loads(outcome["stdout"].strip().splitlines()[-1])
    except (ValueError, IndexError):
        return ctx.absent("the web probe produced no JSON: %s"
                          % (outcome["stderr"] or outcome["stdout"])[:300],
                          invocation=outcome["argv"])
    if "error" in payload:
        return ctx.absent("the application would not boot for the web probe: "
                          "%s" % payload["error"], invocation=outcome["argv"])
    return ctx.measured(payload, invocation=outcome["argv"],
                        html_validity=html_validity(ctx, pages),
                        accessibility=accessibility(ctx, workspace, pages))
