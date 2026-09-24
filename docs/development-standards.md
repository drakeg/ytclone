# Development Standards

This document defines the default engineering workflow for VideoShare/YTClone. It is a living project standard and should be updated whenever the repository's development process changes.

## Sprint workflow

Every meaningful change is delivered as a focused sprint.

1. Review the current implementation, tests, documentation, open work, and relevant architecture before changing code.
2. Write or update the sprint document before application code. Record the goal, scope, acceptance criteria, verification commands, and explicit exclusions.
3. Create a focused branch from current `main`.
4. Implement the smallest coherent change that satisfies the sprint.
5. Add or update regression tests in the same sprint. Tests and documentation are implementation work, not follow-up cleanup.
6. Keep local/Docker verification instructions accurate.
7. Open a draft pull request and keep it draft while required CI is incomplete or failing.
8. Fix CI failures at their root cause. Do not weaken valid tests merely to obtain a green pipeline.
9. Mark the PR ready only after required checks pass.
10. The repository owner performs the merge unless explicitly delegated.
11. After merge, verify the merge state and continue to the next logical sprint without requiring a separate planning/approval round.

## Definition of Done

A sprint is done only when all applicable items are satisfied:

- behavior matches documented acceptance criteria;
- security/privacy boundaries remain intact;
- focused regression tests cover new behavior and important edge cases;
- existing tests are updated when behavior intentionally changes;
- Django/system configuration checks pass;
- migration drift is checked;
- the full automated test suite passes;
- Docker Compose configuration is valid;
- the Docker test path is run when a Docker daemon is available, or the environmental limitation is explicitly recorded;
- sprint/project documentation reflects the actual implementation;
- no unrelated formatting or refactoring churn is introduced;
- CI on the final PR head is green before readiness.

## Coding standards

### General

- Prefer small, focused modules and changes over broad rewrites.
- Preserve existing behavior unless the sprint explicitly changes it.
- Keep functions narrow and name helpers/constants for their intent.
- Avoid duplicated business logic; place reusable behavior in services/helpers.
- Use deterministic ordering with stable tie-breakers when paginating querysets.
- Bound user-controlled query/filter/sort values and provide safe defaults.
- Prefer framework utilities such as `reverse`, `urlencode`, Django forms/querysets, and decorators over hand-built equivalents.
- Mutating endpoints must use the appropriate HTTP method and CSRF protection.
- Do not introduce dependencies, infrastructure, paid services, AWS resources, workers, queues, or schema changes unless the sprint requires and documents them.

### Django and data access

- Enforce authorization and ownership in the queryset/service boundary, not only in templates.
- Video discovery must respect the repository's visibility rules, normally through `Video.objects.visible_to(user)`.
- Private viewer data must remain scoped to the authenticated viewer.
- Apply visibility/ownership and active filters before pagination.
- Use `select_related`/`prefetch_related` where they prevent avoidable query amplification without obscuring correctness.
- Schema changes require migrations and migration tests/checks.

### Templates and state

- Preserve active search/filter/sort/page state across pagination and item-level actions when that state remains meaningful.
- Escape/query-encode user-controlled URL values using Django/template or Python URL utilities.
- Keep empty states accurate for filtered versus genuinely empty collections.
- Keep controls labeled and accessible.

## Testing standards

Every sprint should add focused tests proportional to its risk.

At minimum, consider:

- happy path;
- authentication/authorization and owner isolation;
- visibility boundaries;
- invalid or malformed input fallback;
- boundary values;
- composition of search/filter/sort;
- filter-before-pagination behavior;
- pagination state preservation;
- mutation redirect/state preservation;
- empty-state behavior;
- explicit assertions for every bounded option, rather than assuming one option proves all options.

Do not rely only on a full-suite pass. Run the focused test module first when practical so failures are attributable.

## Standard verification

For Django work, the normal baseline is:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test <focused-test-module>
python manage.py test --parallel 4
docker compose config --quiet
docker compose run --build --rm test
```

If Docker is unavailable in the execution environment, record that limitation rather than claiming the Docker suite ran.

## CI standards

- CI is part of the implementation.
- Investigate the first meaningful traceback/error; parallel-test secondary errors may be fallout.
- Keep CI efficient and avoid redundant dependency installation or heavyweight checks without a demonstrated benefit.
- Verify the exact final PR-head workflow after any fix or documentation/evidence commit that changes the head.
- Do not infer Actions success from an empty combined-status result.

## Documentation standards

- Maintain sprint documents under `docs/`.
- Keep README, roadmap/handoff documentation, local setup, Docker commands, environment variables, and architecture notes synchronized with behavior.
- Document intentional limitations and explicit non-goals.
- When a test audit exposes a gap in previously shipped behavior, close it in a focused regression sprint rather than silently ignoring it.
- This document is the repository-wide baseline; sprint documents may add stricter requirements but should not silently weaken it.

## Security and privacy baseline

- Treat visibility, ownership, private history, bookmarks, playlists, Watch Later, notifications, and search history as security-sensitive.
- Never trust client-provided ownership or visibility state.
- Scope mutations server-side to the authenticated user and accessible object.
- Avoid exposing private objects through counts, pagination, search, suggestions, or indirect joins.

## Change discipline

A sprint should explicitly state when it does **not** change schema, dependencies, external services, AWS/paid resources, workers/queues, or Terraform. This keeps review boundaries clear and prevents accidental scope expansion.
