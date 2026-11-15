# Evidence-first backlog triage

Garcar Repo Foundry now includes a **read-only** cross-repository backlog inventory. It is
an input to the existing Garcar Friday Progress + Backlog scheduled review, **not**
a privileged agent, auto-merger, or a replacement command center.

## Run against reachable GitHub repositories

Authenticate with your existing GitHub CLI, then run:

```bash
python3 scripts/backlog_triage.py --live --output .backlog-evidence
```

This queries open pull requests and GitHub issues across repositories accessible
to the authenticated `gh` identity, using all result pages up to the GitHub
Search API limit of 1,000. **It does not establish access to every private repo.**
Missing pages, duplicate results, API errors or result counts above the search
limit are never labeled complete. The process exits nonzero on partial coverage.

To incorporate a separately authorized Linear issue export, use
`--linear-json /path/to/linear-issues.json`. It accepts `{"issues":[...]}`
from the connected Linear tool. Completed, canceled and duplicate Linear records
are excluded from the active queue. Linear pagination is **the exporter's**
responsibility; the report labels it "supplied snapshot only."

To analyze a known JSON capture without network access:

```bash
python3 scripts/backlog_triage.py --snapshot /path/to/github-search-snapshot.json --output .backlog-evidence
```

The snapshot needs keys `github_prs` and `github_issues`; each contains
`{"total_count": N, "items": [...], "complete": true/false}`.

## Outputs

- `.backlog-evidence/backlog.json`: evidence-linked items, categories and coverage.
- `.backlog-evidence/TRIAGE.md`: prioritized first 40 items and counts.

**Never commit `.backlog-evidence`**: accessible private issue titles, internal
project work and customer references can appear in the generated report. The
directory is ignored by Git. Do not upload it or share across assistants without
specific content and destination approval.

## Scope and security

The script executes only `gh api -X GET` for GitHub discovery; no mutations,
PR merges, issue closures, customer messaging, payment actions, deployments,
or credential edits. The optional Linear input is local. Classification is
**triage, not a claim that an issue has been fixed**.

The separate ChatGPT Friday review may create narrowly scoped draft PRs only
when existing access, test results and owner authorization support them. It must
not auto-merge or deploy. GitHub Actions startup failures still block trustworthy
hosted CI results.

## Validate offline

```bash
python3 -m unittest discover -s tests -p test_backlog_triage.py -v
```

This validates pagination, false-completeness detection, risk categories,
CLI output and the read-only contract. It does not prove GitHub private
repository access, production health or successful customer transactions.
