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