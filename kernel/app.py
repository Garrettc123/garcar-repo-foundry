"""Garcar fleet kernel — every stamped repo exposes the same contract."""
from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

SYSTEM_ID = os.getenv("GARCAR_SYSTEM_ID", "garcar-unspecified")
SYSTEM_ROLE = os.getenv("GARCAR_SYSTEM_ROLE", "satellite")
VERSION = "1.0.0-foundry"

SKUS = [
    {
        "id": "lead-leak-audit",
        "name": "Contractor Lead Leak Audit",
        "price_usd": 47,
        "interval": "one_time",
        "checkout": "https://buy.stripe.com/dRm8wPbb72pY2Mz8BR43S1D",
        "sla_hours": 48,
        "fulfillment": "email-map",
    },
    {
        "id": "revenue-recovery-sprint",
        "name": "Revenue Recovery Sprint",
        "price_usd": 497,
        "interval": "week",
        "checkout": "https://buy.stripe.com/aFa8wPdjfggO3QDcS743S1F",
        "sla_hours": 168,
        "fulfillment": "sprint-map",
    },
    {
        "id": "ai-growth-engine",
        "name": "AI Growth Engine",
        "price_usd": 1497,
        "interval": "month",
        "checkout": "https://buy.stripe.com/9B63cv4MJ9Sq1Iv19p43S1E",
        "sla_hours": 720,
        "fulfillment": "retainer",
    },
]

STOREFRONT = "https://garrettc123.github.io/"

app = FastAPI(title=f"Garcar · {SYSTEM_ID}", version=VERSION)


class FulfillmentIn(BaseModel):
    sku_id: str
    buyer_email: str
    shop_name: str | None = None
    vertical: str | None = "trades"
    stripe_session_id: str | None = None


@app.get("/health")
def health():
    return {
        "ok": True,
        "system": SYSTEM_ID,
        "role": SYSTEM_ROLE,
        "version": VERSION,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/sku")
def sku():
    return {"system": SYSTEM_ID, "storefront": STOREFRONT, "skus": SKUS}


@app.get("/offer")
def offer():
    return RedirectResponse(SKUS[0]["checkout"], status_code=302)


@app.get("/")
def root():
    return {
        "system": SYSTEM_ID,
        "role": SYSTEM_ROLE,
        "contract": ["/health", "/sku", "/offer", "/fulfill"],
        "storefront": STOREFRONT,
        "primary_sku": SKUS[0]["id"],
    }


@app.post("/fulfill")
def fulfill(body: FulfillmentIn):
    sku = next((s for s in SKUS if s["id"] == body.sku_id), None)
    if sku is None:
        return {"ok": False, "error": "unknown_sku", "allowed": [s["id"] for s in SKUS]}
    return {
        "ok": True,
        "status": "queued",
        "system": SYSTEM_ID,
        "sku": sku,
        "buyer_email": body.buyer_email,
        "shop_name": body.shop_name,
        "vertical": body.vertical,
        "stripe_session_id": body.stripe_session_id,
        "sla_hours": sku["sla_hours"],
        "note": "Kernel accepted the job. Wire SMTP in the CASH receiver, not here.",
    }
