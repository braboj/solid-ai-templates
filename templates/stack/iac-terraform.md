# Stack — Terraform Infrastructure
[DEPENDS ON: templates/base/core/git.md, templates/base/core/docs.md, templates/base/core/quality.md, templates/base/infra/cicd.md, templates/base/security/devsecops.md]

Rules for managing cloud infrastructure with Terraform. Covers module design,
remote state, workspaces, variable handling, security, CI/CD integration,
and testing.

---

## Stack
[ID: terraform-stack]

- Language: HCL (Terraform 1.6+)
- Provider: [AWS / Azure / GCP / other]
- State backend: [S3 + DynamoDB / Azure Blob / GCS / Terraform Cloud]
- Module registry: [Terraform Registry / private registry / local]
- Linter: `tflint` + provider-specific ruleset
- Security scanner: `tfsec` or `checkov`
- Test framework: `terratest` (Go) or `terraform test` (native, 1.6+)
- CI/CD: [GitHub Actions / GitLab CI / Atlantis]

---

## Project structure
[ID: terraform-structure]

```
modules/
  [resource-group]/          # reusable, versioned module
    main.tf
    variables.tf
    outputs.tf
    versions.tf              # required_providers and terraform version constraint
    README.md
environments/
  dev/
    main.tf                  # root module for dev
    variables.tf
    terraform.tfvars         # non-sensitive defaults (committed)
    backend.tf               # remote state config
  staging/
    ...
  production/
    ...
.terraform.lock.hcl          # provider version lock — always committed
.tflint.hcl
.tfsec/
  config.yml
Makefile
README.md
CLAUDE.md
```

---

## Module design
[ID: terraform-modules]

- One module per logical resource group (e.g. `vpc`, `rds`, `ecs-service`) —
  not one module per Terraform resource type
- Modules are versioned and sourced by tag — never reference a module
  by a mutable branch name in production
- Keep modules focused: if a module requires more than ~10 input variables,
  it is doing too much — split it
- Output only what callers need — do not expose internal resource attributes
  unless they are genuinely consumed by other modules
- All modules have a `versions.tf` with `required_providers` and a
  `required_version` constraint — callers must not silently upgrade providers

---

## Variables and secrets
[ID: terraform-variables]

- All inputs declared in `variables.tf` with `type`, `description`, and
  `default` (where safe) — never undeclared `var.*` references
- Sensitive variables marked with `sensitive = true` — Terraform redacts
  them from plan output
- Never store secrets in `terraform.tfvars` or any committed file —
  inject via environment variables (`TF_VAR_*`) or a secrets manager
  (Vault, AWS Secrets Manager, Azure Key Vault)
- `terraform.tfvars` committed only for non-sensitive defaults —
  document which vars must be supplied at runtime

---

## State management
[ID: terraform-state]

- Remote state backend required for all non-local environments —
  never use local state in staging or production
- State locking enabled (DynamoDB for S3, built-in for GCS/Azure Blob) —
  prevents concurrent applies
- One state file per environment — never share state between dev, staging,
  and production
- Never edit state files manually — use `terraform state mv`,
  `terraform state rm`, and `terraform import` for state surgery
- State backend bootstrap (S3 bucket, DynamoDB table) managed separately
  from application infrastructure — chicken-and-egg problem if it is not

---

## Workspaces
[ID: terraform-workspaces]

- Use directory-per-environment (`environments/dev/`, `environments/prod/`)
  over Terraform workspaces — workspaces share a backend config and are
  harder to audit and permission separately
- If workspaces are used: name them to match the environment
  (`dev`, `staging`, `production`) — never `default` in production

---

## Terraform conventions
[ID: terraform-conventions]

- `main.tf`: resource definitions
- `variables.tf`: all input variables
- `outputs.tf`: all outputs
- `versions.tf`: provider and Terraform version constraints
- `locals.tf` (optional): computed values used in multiple places
- No resource definitions in `variables.tf` or `outputs.tf` — strict separation
- Resource names in `snake_case` matching the resource purpose:
  `aws_s3_bucket.terraform_state`, not `aws_s3_bucket.bucket1`
- Tags / labels on every resource: at minimum `environment`, `project`,
  `managed_by = "terraform"`
- `terraform fmt` run before every commit — CI rejects unformatted code

---

## Security
[ID: terraform-security]
[EXTEND: base-devsecops]

- Run `tfsec` or `checkov` in CI on every PR — block merge on HIGH severity findings
- No hardcoded credentials, ARNs containing account IDs, or IP addresses
  in committed `.tf` files — use variables and data sources
- IAM policies follow least privilege — no `"*"` actions or resources
  without a documented exception
- Encryption at rest and in transit enabled for all storage resources —
  `encrypted = true`, `kms_key_id` where applicable
- Public access blocked by default — explicitly enabled only when required,
  with a comment explaining why

---

## CI/CD workflow
[ID: terraform-cicd]
[EXTEND: base-cicd]

- PR pipeline: `terraform init` → `terraform validate` → `tflint` →
  `tfsec` → `terraform plan` (output posted as PR comment)
- Merge to main: `terraform apply -auto-approve` (for dev) or
  manual approval gate (for staging/production)
- Never run `terraform apply` from a local machine against staging or
  production — all applies go through CI
- Plan output stored as an artifact — apply uses the saved plan, not a
  fresh one, to prevent drift between plan and apply
- Use Atlantis or Terraform Cloud for PR-based workflow with apply locks
  if the team size justifies it

---

## Testing
[ID: terraform-testing]

- `terraform validate`: always — catches syntax and type errors
- `terraform plan`: always in CI — review plan output before apply
- Native `terraform test` (1.6+): unit-test module logic with mock providers —
  no real cloud resources needed
- `terratest` (Go): integration tests that provision real resources,
  assert on outputs, then destroy — run in a dedicated test environment,
  not production
- Always run `terraform destroy` at the end of integration tests —
  clean up to avoid cost and drift

---

## Git conventions
[EXTEND: base-git]

- `.terraform.lock.hcl` is committed — ensures reproducible provider versions
- `.terraform/` directory is gitignored — downloaded providers are not committed
- `*.tfvars` files containing secrets are gitignored — document the required
  vars in `README.md` or a `.tfvars.example` file
- Plan files (`.tfplan`) are gitignored — they may contain sensitive values

---

## Commands
```
terraform init                   # initialise working directory and download providers
terraform validate               # validate configuration syntax and types
terraform plan -out=tfplan        # generate and save execution plan
terraform apply tfplan            # apply the saved plan
terraform destroy                 # destroy all managed resources
terraform fmt -recursive          # format all .tf files
tflint                            # lint with tflint rules
tfsec .                           # security scan
```