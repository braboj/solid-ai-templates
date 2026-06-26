# Stack — gRPC Service (Python)
[DEPENDS ON: templates/base/core/git.md, templates/base/core/docs.md, templates/base/core/quality.md, templates/base/core/config.md, templates/backend/grpc.md, templates/backend/concurrency.md, templates/stack/python-lib.md, templates/base/infra/cicd.md, templates/base/security/devsecops.md]

Extends the Python library stack and the gRPC backend layer with Python-specific
conventions for implementing async gRPC servers and clients.

---

## Stack
[ID: grpc-python-stack]

- Language: Python 3.11+
- gRPC library: `grpcio` + `grpcio-aio` (async) + `grpcio-tools`
- Proto tooling: `buf` (preferred) or `grpc_tools.protoc`
- Package manager: [uv / pip / poetry]
- Linter: ruff
- Formatter: ruff format
- Type checker: mypy (strict mode)
- Test runner: pytest + `pytest-asyncio`
- Distribution: Docker image

---

## Project structure
[ID: grpc-python-structure]

```
src/
  [app_name]/
    __init__.py
    server.py            # gRPC server bootstrap and graceful shutdown
    config.py            # pydantic-settings BaseSettings
    servicers/
      [feature].py       # implements generated servicer base class
    services/
      [feature].py       # business logic — no grpc imports
    interceptors/
      auth.py
      logging.py
generated/
  [org]/[service]/v1/    # generated stubs — never edit by hand
    [service]_pb2.py
    [service]_pb2_grpc.py
proto/
  [org]/[service]/v1/
    [service].proto
tests/
  conftest.py
  test_[feature].py
pyproject.toml
buf.yaml
buf.gen.yaml
.env.example
Dockerfile
README.md
CLAUDE.md
```

---

## Service implementation
[EXTEND: grpc-implementation]

- Servicer classes extend the generated `[Service]Servicer` base class
- Use `grpc.aio` throughout — all servicer methods are `async def`
- Inject dependencies via `__init__` — never import service singletons
  at module level
- Access request metadata with `context.invocation_metadata()`
- Set response status codes with `await context.abort(grpc.StatusCode.NOT_FOUND,
  "detail")`

---

## Server setup and shutdown
[EXTEND: backend-concurrency]

- Create the server with `grpc.aio.server()` in an async `main()`
- Add servicers and interceptors before `await server.start()`
- Graceful shutdown: listen for `SIGTERM`, call `await server.stop(grace=30)`
- Use `asyncio.run(main())` as the entry point in `server.py`

---

## Interceptors
[EXTEND: grpc-interceptors]

- Implement `grpc.aio.ServerInterceptor` — override `intercept_service()`
- Chain interceptors as a list in `grpc.aio.server(interceptors=[...])`
- Access metadata in interceptors via `handler_call_details.invocation_metadata`

---

## Testing
[EXTEND: grpc-testing]

- Use `grpc.aio.insecure_channel()` pointed at an in-process test server
  started with a random free port
- `pytest-asyncio` with `asyncio_mode = "auto"` in `pyproject.toml`
- No mocking of the gRPC channel — test through a real in-process server
- Test naming: `test_<method_name>_<state>_<expected>`
  e.g. `test_get_user_not_found_returns_not_found_status`
- Run before every commit: `pytest && mypy src/ --strict`

---

## Commands
```
buf lint                          # lint proto files
buf generate                      # generate Python stubs
python -m grpc_tools.protoc ...   # alternative stub generation
python -m [app_name].server       # run server
pytest                            # run tests
mypy src/ --strict                # type check
ruff check src/ tests/            # lint
```