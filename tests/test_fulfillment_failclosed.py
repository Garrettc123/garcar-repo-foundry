"""Unit tests prevent false fulfillment acceptance by any candidate kernel."""
import unittest

from fastapi import HTTPException
from fastapi.testclient import TestClient
from kernel.app import FulfillmentIn, app, fulfill


class StubFulfillmentTests(unittest.TestCase):
    def test_direct_fulfillment_denied_without_payment_or_queue(self):
        with self.assertRaises(HTTPException) as ctx:
            fulfill(FulfillmentIn(sku_id="lead-leak-audit",
                                  buyer_email="buyer@example.test",
                                  stripe_session_id="cs_test_not_paid"))
        self.assertEqual(ctx.exception.status_code, 503)

    def test_http_fulfillment_not_queued(self):
        client = TestClient(app)
        response = client.post("/fulfill", json={
            "sku_id": "lead-leak-audit",
            "buyer_email": "buyer@example.test",
            "stripe_session_id": "cs_test_unverified",
        })
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("queued", response.text.lower())
        self.assertNotIn("accepted", response.text.lower())


if __name__ == "__main__":
    unittest.main()
