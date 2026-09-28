# Garcar Repo Foundry

Builds every repo Garrettc123 owns into a **runnable kernel**.

This is not another $50M ARR README. It is the compiler for the fleet.

## Fleet snapshot (2026-09-27)

| Tier | Count | Meaning |
|---|---|---|
| CASH | 19 | Touches Stripe, leads, fulfillment, storefront |
| CONTROL | 11 | Hub, base contract, RHNS, production stack |
| CODE | 26 | Has real source beyond a stub |
| STUB | 140 | Thin repo, usually README + placeholder |
| EMPTY | 88 | No language, almost no bytes |
| **Total** | **284** | Owned by `Garrettc123` |

Source of truth: [`inventory/FLEET.md`](inventory/FLEET.md) and [`inventory/repos.json`](inventory/repos.json).

## What "build every repo" means here

1. Every repo gets the same contract: `/health`, `/sku`, `/offer`, `/fulfill`.
2. CASH repos get the live $47 / $497 / $1,497 Stripe links, not fake pipeline numbers.
3. STUB and EMPTY repos get a kernel stamp instead of a new mythology file.
4. CONTROL repos stay the orchestration layer. Do not flatten them into landing pages.

## Live SKUs

| Offer | Price | Checkout |
|---|---|---|
| Contractor Lead Leak Audit | $47 | https://buy.stripe.com/dRm8wPbb72pY2Mz8BR43S1D |
| Revenue Recovery Sprint | $497/wk | https://buy.stripe.com/aFa8wPdjfggO3QDcS743S1F |
| AI Growth Engine | $1,497/mo | https://buy.stripe.com/9B63cv4MJ9Sq1Iv19p43S1E |

Storefront: https://garrettc123.github.io/

Do not charge the live $47 link with card 4242.

## Run the kernel locally

```bash
cd kernel
pip install -r requirements.txt
GARCAR_SYSTEM_ID=garcar-repo-foundry uvicorn app:app --port 8080
curl localhost:8080/health
curl localhost:8080/sku
```

## Stamp a target repo

```bash
python scripts/stamp.py --repo NAME --dry-run
python scripts/stamp.py --repo NAME
```

`scripts/stamp.py` refuses to stamp protected cash/control repos without `--force`.
