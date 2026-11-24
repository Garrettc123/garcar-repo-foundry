"""Regression tests for fleet truthfulness; never infer shipping from a stub."""
import json
from pathlib import Path

import pytest
from fastapi import HTTPException

from kernel.app import FulfillmentIn, fulfill

ROOT = Path(__file__).resolve().parents[1]


def test_foundry_cannot_claim_durable_fulfillment():
    with pytest.raises(HTTPException) as raised:
        fulfill(FulfillmentIn(
            sku_id="lead-leak-audit",
            buyer_email="someone@example.test",
            stripe_session_id="cs_test_dummy",
        ))
    assert raised.value.status_code == 503
    assert "no fulfillment queue" in raised.value.detail


def test_sha_resolved_registry_is_complete_and_not_certifying():
    data = json.loads((ROOT / "inventory" / "VERIFIED_20261105.json").read_text())
    assert data["repository_count"] == 8
    assert data["release_gate"] == "BLOCKED"
    assert len(data["repositories"]) == 8
    assert len({r["name"] for r in data["repositories"]}) == 8
    assert all(len(r["base_sha"]) == 40 for r in data["repositories"])
    assert all(r["evidence_status"] != "deployed_and_revenue_verified" for r in data["repositories"])
    assert data["candidate_canonical_roles"]["payment_capture_and_fulfillment"] == "garcar-payments"
