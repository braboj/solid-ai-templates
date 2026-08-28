# Base — TypeScript
[ID: base-typescript]
[DEPENDS ON: templates/base/core/quality.md]

## Type design
[ID: base-typescript-type-design]

- Use `interface` for object shapes; use `type` for unions and aliases
- Use discriminated unions (tagged unions) for type families — a literal
  `type` or `kind` field plus a union is safer than class hierarchies
- Compose sub-interfaces when a domain has multiple categories with
  different fields; keep single-purpose types flat
- When declaring data arrays that use a discriminated union, type each
  section with its specific sub-interface (`FlashItem[]`), not the
  broad union (`Item[]`) — spread into the union array at the end
- No enums — use `as const` objects or string literal unions
- No `any` — use `unknown` and narrow, or define a proper type

## Naming
[ID: base-typescript-naming]

- Booleans: prefix with `is`, `has`, or `can` (`isActive`, `hasPermission`)
- Import types with `import type { ... }`
- Explicit return types on non-trivial functions

## Comments
[ID: base-typescript-comments]

- Prefer self-documenting names — a field that needs a comment needs a
  better name
- Use inline comments for units that cannot be encoded in the name:
  `weight: number; // grams` not a standalone `// Grams` above the field
- Keep inline comments lowercase, short, and consistent across the interface

## Strictness
[ID: base-typescript-strictness]

- `strict: true` — no exceptions
- Follow `@typescript-eslint/recommended`

## Testing
[ID: base-typescript-testing]

- Test factory defaults for optional fields MUST be `undefined` (omitted),
  not convenient values like `false` or `0` — explicit defaults mask bugs
  that only appear with real data shapes
- Data validation tests SHOULD flag boolean fields where one branch (`true`
  or `false`) has zero occurrences across the dataset — this is a data
  smell that can silently break sorting, filtering, and UI logic

## Tooling
[ID: base-typescript-tooling]

`base-quality-gates` states which categories a project MUST gate; this
table names the TypeScript tool that satisfies each. Stack templates add
only the tools their shape changes.

| Category              | Tool                     | Config              |
| --------------------- | ------------------------ | ------------------- |
| Commit-hook framework | `husky` + `lint-staged`  | `.husky/`           |
| Lint                  | `eslint`                 | `eslint.config.js`  |
| Format                | `prettier`               | `.prettierrc`       |
| Type check            | `tsc --noEmit`           | `tsconfig.json`     |
| Cognitive complexity  | `eslint-plugin-sonarjs`  | `eslint.config.js`  |
| Package manifest      | `package.json`           | —                   |

- `husky` installs the git hook; `lint-staged` scopes each check to the
  staged files. Neither alone is the Layer-2 gate — a `husky` hook that
  lints the whole tree is slow enough that contributors bypass it
- Cognitive complexity MUST be gated by `eslint-plugin-sonarjs`. Core
  ESLint has no cognitive-complexity rule, so the category has no
  TypeScript binding without the plugin
- `tsc` runs with `strict: true`, per `base-typescript-strictness`. The
  type gate and the editor's checker MUST be the same tool at the same
  strictness, per `quality-gates-layers`
