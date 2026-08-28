# Base — Python
[ID: base-python]
[DEPENDS ON: templates/base/core/quality.md]

Per-language tool selection for Python. `base-quality-gates` states which
categories a project MUST gate and at which layer; this file names the
Python tool that satisfies each. Stack templates add only the tools their
shape changes — a library's build and publish step, a service's runtime
checks — and do not re-declare the bindings below.

## Tooling
[ID: base-python-tooling]

| Category              | Tool                        | Config                    |
| --------------------- | --------------------------- | ------------------------- |
| Commit-hook framework | `pre-commit`                | `.pre-commit-config.yaml` |
| Lint                  | `ruff`                      | `pyproject.toml`          |
| Format                | `ruff format`               | `pyproject.toml`          |
| Type check            | `mypy` (strict)             | `pyproject.toml`          |
| Cognitive complexity  | `complexipy`                | `pyproject.toml`          |
| Security (SAST)       | `bandit`                    | `pyproject.toml`          |
| Tests                 | `pytest`                    | `pyproject.toml`          |
| Coverage              | `pytest-cov`                | `pyproject.toml`          |
| Docstrings            | `ruff` `D` rules            | `pyproject.toml`          |
| Package manifest      | `pyproject.toml`            | —                         |

- `ruff` MUST be the single lint and format tool. It subsumes flake8,
  isort, pyupgrade and most of pylint, so a project carrying those
  alongside it runs overlapping rule sets that disagree at the margins
- Cognitive complexity MUST be gated by a separate tool. `ruff` has no
  cognitive-complexity rule — its `C901` is McCabe, which measures a
  different thing — so the category has no Python binding without
  `complexipy`
- Tool configuration MUST live in `pyproject.toml`. Splitting it across
  `setup.cfg`, `tox.ini` or `.flake8` gives one tool two config sources
  whose precedence is tool-specific, and a rule edited in the losing file
  reads as applied
- `mypy` runs in strict mode. A non-strict run passes on unannotated
  code, so the gate reports success over the code least covered by it
- The coverage tool is named here; the threshold is not. The number and
  its escalation policy belong to `quality-gates-thresholds`, which
  governs every language

