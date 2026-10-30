#!/usr/bin/env python3
"""Post-deployment verification against a live deployment.

Exercises the real HTTP surface: health contract, order creation, the
discount boundary, validation rejection, retrieval and 404 handling.
Writes a machine-readable result file and exits non-zero on any failure.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Callable, List

import httpx

TIMEOUT = httpx.Timeout(30.0)


class Checks:
    def __init__(self, base_url: str, expected_version: str) -> None:
        self.client = httpx.Client(base_url=base_url.rstrip("/"), timeout=TIMEOUT)
        self.expected_version = expected_version
        self.results: List[dict] = []

    def run(self, name: str, fn: Callable[[], str]) -> bool:
        try:
            detail = fn()
            self.results.append({"check": name, "status": "PASS", "detail": detail})
            print(f"[PASS] {name} :: {detail}")
            return True
        except Exception as exc:  # noqa: BLE001 - verification must report every failure mode
            self.results.append({"check": name, "status": "FAIL", "detail": str(exc)})
            print(f"[FAIL] {name} :: {exc}")
            return False

    # --- individual checks -------------------------------------------------
    def health(self) -> str:
        response = self.client.get("/health")
        assert response.status_code == 200, f"expected 200, got {response.status_code}"
        body = response.json()
        assert body["status"] == "healthy", f"unexpected status: {body}"
        assert body["service"] == "order-management-service", f"unexpected service: {body}"
        if self.expected_version:
            assert body.get("version") == self.expected_version, (
                f"expected version {self.expected_version}, got {body.get('version')}"
            )
        return f"status={body['status']} version={body.get('version')}"

    def create_order_no_discount(self) -> str:
        response = self.client.post(
            "/orders", json={"product_name": "Smoke Widget", "quantity": 2, "unit_price": 50}
        )
        assert response.status_code == 201, f"expected 201, got {response.status_code}"
        body = response.json()
        assert Decimal(body["total"]) == Decimal("100.00"), f"total={body['total']}"
        assert body["discount_applied"] is False
        return f"id={body['id']} total={body['total']}"

    def discount_boundary(self) -> str:
        response = self.client.post(
            "/orders", json={"product_name": "Boundary Widget", "quantity": 10, "unit_price": 100}
        )
        assert response.status_code == 201, f"expected 201, got {response.status_code}"
        body = response.json()
        assert body["discount_applied"] is True, "subtotal of exactly 1000 must be discounted"
        assert Decimal(body["total"]) == Decimal("900.00"), f"total={body['total']}"
        return f"subtotal=1000.00 total={body['total']} (10% applied at boundary)"

    def retrieve_existing(self) -> str:
        created = self.client.post(
            "/orders", json={"product_name": "Retrieve Widget", "quantity": 1, "unit_price": 10}
        ).json()
        response = self.client.get(f"/orders/{created['id']}")
        assert response.status_code == 200, f"expected 200, got {response.status_code}"
        assert response.json()["id"] == created["id"]
        return f"retrieved id={created['id']}"

    def retrieve_missing(self) -> str:
        response = self.client.get("/orders/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404, f"expected 404, got {response.status_code}"
        return "unknown id correctly returned 404"

    def validation_rejected(self) -> str:
        response = self.client.post(
            "/orders", json={"product_name": "Bad Widget", "quantity": 0, "unit_price": 10}
        )
        assert response.status_code == 422, f"expected 422, got {response.status_code}"
        return "quantity=0 correctly rejected with 422"


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a live Order Management Service deployment.")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--expected-version", default="")
    parser.add_argument("--output", default="verification-results.json")
    args = parser.parse_args()

    checks = Checks(args.base_url, args.expected_version)
    outcomes = [
        checks.run("health endpoint", checks.health),
        checks.run("create order without discount", checks.create_order_no_discount),
        checks.run("discount boundary subtotal == 1000", checks.discount_boundary),
        checks.run("retrieve existing order", checks.retrieve_existing),
        checks.run("retrieve missing order returns 404", checks.retrieve_missing),
        checks.run("invalid quantity returns 422", checks.validation_rejected),
    ]

    passed = all(outcomes)
    report = {
        "baseUrl": args.base_url,
        "expectedVersion": args.expected_version,
        "verifiedUtc": datetime.now(timezone.utc).isoformat(),
        "overall": "PASS" if passed else "FAIL",
        "passed": sum(outcomes),
        "total": len(outcomes),
        "checks": checks.results,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2))
    print(f"\n{report['overall']}: {report['passed']}/{report['total']} checks -> {output}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
