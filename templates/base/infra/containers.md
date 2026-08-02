# Base — Containers
[ID: base-containers]

## Dockerfile conventions
- Use official, minimal base images (e.g. `alpine`, `slim`, `distroless`)
- Pin base images to a specific version tag — never use `latest`
- Use multi-stage builds: build in one stage, copy only the final artifact
  into a minimal runtime image
- Exclude dev dependencies, build tools, and test files from the final image
- Each `RUN` instruction should do one logical thing — chain related commands
  with `&&` to minimise layers
- Copy only what is needed — use `.dockerignore` to exclude everything else

## Runtime security
- MUST run containers as a non-root user — create and switch to a dedicated
  application user in the Dockerfile
- Set the filesystem to read-only where possible (`--read-only`)
- Never run containers in privileged mode unless absolutely required and
  explicitly justified
- Drop all Linux capabilities and add back only those required
- Do not store secrets in environment variables baked into the image — inject
  at runtime from a secret vault

## Resource management
- MUST define CPU and memory requests and limits for every container
- Set requests to the typical workload; set limits to the safe maximum
- Never set memory limit lower than memory request
- Monitor resource usage and adjust limits based on observed behaviour —
  do not guess

## Image hygiene
- Scan all images for vulnerabilities in CI before pushing to a registry
- Never push an image with **fixable** critical or high vulnerabilities
  to staging or production — an unfixable upstream or base-layer CVE is
  advisory (publish it with an SBOM), not a release blocker
- Tag images with the git commit SHA or release version — never rely on
  mutable tags in staging or production
- Remove unused images from the registry regularly

## Runtime version coherence

Pinning the base image (above), the CI runtime, the type-checker target,
and the packaging floor are four separate loci for the SAME runtime
version. Pin them independently and a base-image-only bump — often a
lone dependency-bot PR — ships an image on the new runtime while every
gate still validates the old one: the gates go green and an untested
runtime ships.

- The language / runtime version MUST be identical across the container
  base image tag or digest, every CI job that sets up the runtime, the
  static type-checker's target version, and the packaging metadata floor
  (`requires-python`, `engines`, equivalent)
- Move it in one coordinated change; reject an isolated base-image bump
  that leaves the gates behind — what is tested MUST be what ships
- One exception, documented inline: a formatter or linter `target-version`
  MAY trail one minor as a style floor when the newer target introduces
  a confusing auto-rewrite

## Docker Compose (if applicable)

Use a `docker-compose.yml` (Compose file) when a single image is not
enough: more than one service (app plus datastore or cache), or an
isolated build/run environment for a toolchain impractical to install
on the host. Not every project needs Compose — keep it to those cases.

- Define each service, its image or build context, ports, and
  dependencies (`depends_on`) in the Compose file; keep it at the repo
  root alongside the `Dockerfile`
- Local dev: `docker compose build` then `docker compose run --rm
  <service>` (or `up`) — `--rm` cleans up the one-off container so
  repeated runs do not accumulate stopped containers
- Bind-mount the source for local dev so edits are live without a
  rebuild; do NOT bind-mount in CI or production — there the image is
  the artifact, and a mount would shadow it with host files
- An image that installs the project's own package in editable mode
  bakes an absolute package path at build time. When the source is
  bind-mounted over the workdir, a later layout change — a flat to
  `src/` migration — leaves that baked path pointing at a directory
  that no longer exists, so the import fails while the live code sits
  under the mount. Resolve the package by an explicit source path
  instead of the baked finder, and assert the import at build time so
  a broken layout fails the build rather than every run:

```dockerfile
RUN pip install -e ".[accel,dev]"

# Resolve by the live location, not the path the editable finder baked
ENV PYTHONPATH=/app/src

# Fail the build, not the run
RUN python -c "import pkg, heavy_dep"
```

- A write inside a `--rm` container is discarded on exit, and a write
  to data baked into the image at build time never reaches the host or
  a later build. Document where a state-mutating command's write lands
  and route the reader to a boundary that persists. A quickstart that
  shows such a command under `run --rm` misleads silently: the reader
  runs it, sees it succeed, and the state reverts on the next run. For
  a one-off, prefer the alternative that needs no write at all — pass
  the value inline:

```text
run --rm (ephemeral)   bind-mount host path   edit source + rebuild
write -> top layer     write -> host file     write -> next image
gone on exit           persists               persists (shipped)
```

- Compose orchestrates local and single-host multi-service dev;
  production multi-service orchestration is Kubernetes (below)

## Orchestration (Kubernetes)
- Define all Kubernetes resources as code — no `kubectl apply` from a local
  machine in production
- Use namespaces to separate environments and teams
- MUST run at least two replicas of every service in staging and production
- Use liveness and readiness probes — readiness probe MUST pass before a pod
  receives traffic
- Use `PodDisruptionBudget` to guarantee availability during rolling updates
- Never store configuration or secrets in ConfigMaps as plain text — use
  secret management integration (e.g. external secrets operator)