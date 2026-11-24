# Garcar Repo Foundry

Provides candidate starter kernels and a read-only completion evidence gate. **A generated kernel, README, or listed repository is not evidence that a system is runnable, deployed, secure, profitable, or production-ready.**

## Fleet inventory (historical snapshots)

The latest incorporated dated enumeration is **329 repositories, observed 2026-11-22**, from `inventory/observed_2026-11-22.json`. All runtime states in that inventory were **unverified**. `scripts/completion_matrix.py` produces one fail-closed review state per repository; see `inventory/COMPLETION_GATES.md`.

The tier breakdown below is an **older September 27 snapshot**, not the current total.

### September 27, 2026 snapshot

| Tier | Count | Meaning |
|---|---|---|
| CASH | 19 | Touches Stripe, leads, fulfillment, storefront |
| CONTROL | 11 | Hub, base contract, RHNS, production stack |
| CODE | 26 | Has real source beyond a stub |
| STUB | 140 | Thin repo, usually README + placeholder |
| EMPTY | 88 | No language, almost no bytes |
| **Total** | **284** | Owned by `Garrettc123` |

Old tier references: [`inventory/FLEET.md`](inventory/FLEET.md) and [`inventory/repos.json`](inventory/repos.json). They do not supersede the dated 329-repository inventory.

## What "build every repo" means here

1. A **candidate kernel** can expose standard routes; this does not make each repository deployable or certify fulfillment.
2. Checkout references require independent active Stripe-account and price verification; do not copy historical links into production as proof of a payable SKU.
3. STUB and EMPTY repositories remain incomplete until source, tests, deployment/artifact and actual acceptance evidence exist.
4. CONTROL repos stay the orchestration layer. Do not flatten them into landing pages.

## Historical SKU references (unverified against active payment account)

| Offer | Price | Checkout |
|---|---|---|
| Contractor Lead Leak Audit | $47 | https://buy.stripe.com/dRm8wPbb72pY2Mz8BR43S1D |
| Revenue Recovery Sprint | $497/wk | https://buy.stripe.com/aFa8wPdjfggO3QDcS743S1F |
| AI Growth Engine | $1,497/mo | https://buy.stripe.com/9B63cv4MJ9Sq1Iv19p43S1E |

Historical storefront reference: https://garrettc123.github.io/ — deployment and commerce flow not verified by this README.

Do not charge the live $47 link with card 4242.

## Run the kernel locally

```bash
cd kernel
pip install -r requirements.txt
GARCAR_SYSTEM_ID=garcar-repo-foundry uvicorn app:app --port 8080
curl localhost:8080/health
curl localhost:8080/sku
```

## Generate a local candidate stamp (not a deployment)

```bash
python scripts/stamp.py --repo NAME --dry-run
python scripts/stamp.py --repo NAME
```

`scripts/stamp.py` refuses to stamp protected cash/control repos without `--force`.

**Safety:** The current main-branch foundry kernel's `/fulfill` response is not proof of durable acceptance. Existing draft PR #1 proposes disabling false success responses. Do not deploy stamped kernels or execute checkout links without reconciling those gates.
