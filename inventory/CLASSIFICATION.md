# Classification rules

Applied 2026-11-04 against `gh repo list Garrettc123` (313 unique names).

Rules (in precedence order):
1. **CONTROL** — name/description matches orchestration patterns (hub, control plane, sync core, foundry, orchestrator, RHNS core, architecture, production, sovereign, command center).
2. **CASH** — name/description touches Stripe, checkout, storefront, fulfillment, payment, lead, revenue, monetization, invoice, subscription, CRM, deal, audit.
3. **CODE** — has a primary language and >= 150 KB on disk.
4. **STUB** — has a language or more than 10 KB, but below the CODE bar.
5. **EMPTY** — no language and <= 10 KB.

CASH 53 · CONTROL 28 · CODE 29 · STUB 128 · EMPTY 75.
