# Fleet completion truth gate — 2026-11-24

Scope: a **dated** inventory of 329 GitHub repositories observed on 2026-11-22 through authenticated repository enumeration. Neither historical inventory nor repo naming certifies a working product.

Run locally:

```bash
python -m unittest discover -s tests -p 'test_completion_matrix.py' -v
python scripts/completion_matrix.py \
  --snapshot inventory/observed_2026-11-22.json \
  --output /tmp/garcar-fleet-completion.json
```

For each repository, `scripts/completion_matrix.py` emits a conservative status and explicitly sets `production_ready=false`. Its optional `--evidence` JSON can attach human-reviewed GitHub evidence URLs (source, tests, security, runtime, customer flow) but **only lists pointers**. It does not validate external evidence independently and never promotes a repository to production ready.

Status definitions: `UNINSPECTED` (no evidence), `SOURCE_REVIEW_ONLY` (code reviewed), `CI_EVIDENCE_ONLY` (a test-run URL exists but no verified runtime receipt), `OPERATOR_REVIEW_REQUIRED` (reported links need independent validation), and `ARCHIVED_NOT_CERTIFIED` (not an active release).

### Actual release checklist for every candidate

1. Determine which repository is the owner of the deployed capability; archive/retire redundant candidates by separate review.
2. Inspect source and secret boundaries, build and lock dependencies, run relevant tests and security checks.
3. Verify CI against the **current** commit SHA, not an earlier passing workflow.
4. For a service, verify a real authenticated health/readiness probe and durable storage, with recovery and deployment receipts.
5. For a commercial workflow, verify consent, accurate offer/pricing, authorized paid event, idempotency, and fulfillment evidence.
6. Document explicit blockers. Never fabricate deployment, revenue, accounts, customers, success rates, or agent activity.

### Current known P0 blockers

- `garcar-payments`: latest inspected Integration Health Check failed because both health URL secrets were unset; do not mark production healthy until endpoints and signing credentials are independently verified.
- `garcar-lead-intake`: original branch accepted non-durable leads; see the isolated durability patch PR, and verify persistent volume, backups and privacy policy before production.
- `garcar-repo-foundry`: current main kernel `/fulfill` returns a queued claim without durable persistence. Existing draft PR #1 proposes fail-closed semantics; do not stamp this unsafe kernel onto repositories as proof of fulfillment.
- `garcar-communication-bus`: current root inspection shows README only; no independently verified transport implementation.

This release gate has no credentials, no external network calls, no production writes, no customer operations, and no mass PR creation.
