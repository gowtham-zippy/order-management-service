# PR: Order Management Service — API, discount pricing and multi-stage CI/CD

**Source:** `feature/order-management-service` → **Target:** `main`
**Closes:** #XXX
**Related:** #XX1 #XX2 #XX3 #XX4 #XX5 #XX6 #XX7 #XX8

---

## 1. Summary

Adds the Order Management Service: a FastAPI application that creates and
retrieves orders against a thread-safe in-memory repository, applies a 10%
volume discount when the subtotal reaches 1000, and exposes a health probe.
Ships with 18 unit tests and a seven-stage Azure DevOps pipeline that builds,
tests, packages a versioned artifact, produces a release readiness report,
waits for manual approval, deploys to Azure App Service and verifies the live
deployment.

## 2. What Changed

| Area | Files | Notes |
|---|---|---|
| API | `app/main.py`, `app/routers/orders.py`, `app/routers/health.py` | `POST /orders`, `GET /orders/{id}`, `GET /health` |
| Contracts | `app/models.py` | Pydantic v2 schemas with field-level validation |
| Pricing | `app/pricing.py` | `Decimal` arithmetic; inclusive 1000 discount threshold |
| Storage | `app/storage.py` | Lock-protected in-memory repository |
| Tests | `tests/` | 18 unit tests + live smoke verification script |
| Pipeline | `azure-pipelines.yml`, `pipelines/templates/*` | Build → Test → Package → Readiness → Approval → Deploy → Verify |
| Docs | `README.md`, `docs/**` | Work items, readiness report, release notes, evidence templates |

## 3. Acceptance Criteria Coverage

| AC | Description | Covered by | Status |
|---|---|---|---|
| AC1 | Create order returns 201 with breakdown | `test_subtotal_below_threshold_has_no_discount` | PASS |
| AC2 | Subtotal < 1000 → no discount | `test_subtotal_below_threshold_has_no_discount` | PASS |
| AC3 | Subtotal == 1000 → 10% discount (boundary) | `test_subtotal_exactly_at_threshold_gets_discount` | PASS |
| AC4 | Subtotal > 1000 → 10% discount | `test_subtotal_above_threshold_gets_discount` | PASS |
| AC5 | Validation → 422 | `test_invalid_quantity_is_rejected`, `test_invalid_unit_price_is_rejected`, `test_missing_product_name_is_rejected`, `test_blank_product_name_is_rejected` | PASS |
| AC6 | Retrieve existing order → 200 | `test_existing_order_is_retrieved` | PASS |
| AC7 | Retrieve missing order → 404 | `test_missing_order_returns_404` | PASS |
| AC8 | Health → 200 with version | `test_health_endpoint` | PASS |
| AC9 | Decimal monetary precision | `test_discount_boundary_matrix` | PASS |
| AC10 | Test failure blocks downstream stages | See §5 | PASS |

**Local result:** `18 passed in 0.16s` · flake8 clean.

## 4. Copilot Review Findings and Decisions

| # | Severity | Finding | Decision | Rationale | Verification |
|---|---|---|---|---|---|
| 1 | High | `float` was used for `unit_price` and totals, so `0.1 + 0.2` style drift could surface in currency responses (e.g. a 1000.0000000001 subtotal skipping the discount). | **Accepted** | Money must never be represented in binary floating point. Switched `unit_price` and every derived amount to `Decimal` with `ROUND_HALF_UP` quantisation to 2 places. | `test_discount_boundary_matrix` asserts exact `Decimal` equality at 999.99 / 1000.00 / 1000.01. |
| 2 | High | The discount comparison `subtotal > 1000` excluded the boundary value stated in the acceptance criteria. | **Accepted** | AC3 makes the threshold inclusive. Changed to `>=` and added a dedicated boundary test so the rule cannot silently regress. | `test_subtotal_exactly_at_threshold_gets_discount` → `total == 900.00`. Demonstrated failing under `>` in §5. |
| 3 | Medium | The module-level `dict` backing the repository was mutated without synchronisation; under Uvicorn's threadpool, concurrent writes could interleave. | **Accepted** | Correctness under the default multi-threaded server is a baseline expectation, and a `threading.Lock` costs nothing at this volume. | Repository writes and reads are lock-guarded; suite remains green. |
| 4 | Medium | `GET /orders/{id}` raised a bare `KeyError`, producing a 500 with a stack trace for a routine not-found case. | **Accepted** | Leaking internals is an information-disclosure issue and the wrong status code. Replaced with `HTTPException(404)` carrying a descriptive `detail`. | `test_missing_order_returns_404` asserts both status and message. |
| 5 | Medium | Incrementing integer order IDs were guessable and enabled trivial enumeration of other customers' orders. | **Accepted** | Non-sequential identifiers remove the enumeration primitive at zero cost. Switched to `uuid4`. | IDs returned are UUID4; the 404 test uses a well-formed but absent UUID. |
| 6 | Low | The request model accepted unknown fields silently. | **Accepted** | `extra="forbid"` surfaces client typos (e.g. `unitPrice`) as 422 instead of silently defaulting. | Covered implicitly by the validation suite; schema now rejects unknown keys. |
| 7 | Low | `product_name` of `"   "` passed the `min_length=1` check. | **Accepted** | Whitespace-only names are not valid product names. Added stripping plus an explicit non-blank validator. | `test_blank_product_name_is_rejected` parametrised over `""` and `"   "`. |
| 8 | Medium | Suggested adding a global `try/except Exception` handler returning a generic 500 for all endpoints. | **Rejected** | FastAPI/Starlette already return a 500 without leaking internals when `debug=False`, and a blanket catch-all would swallow genuine defects and make incidents harder to diagnose. Validation and not-found — the two realistic failure modes — are already handled explicitly. | No behavioural change; error paths covered by the 404 and 422 tests. |
| 9 | Low | Suggested replacing the in-memory store with SQLAlchemy and a database. | **Rejected** | The user story explicitly scopes this release to in-memory storage. Introducing a database would expand scope, add infrastructure and credentials, and delay delivery. The constraint is documented in the README and logged as follow-up. | Documented under *Known Limitations*; rollback plan notes no data migration is involved. |
| 10 | Low | Suggested adding `GET /orders` list and `DELETE /orders/{id}` endpoints for completeness. | **Rejected** | Not in the acceptance criteria. Unrequested endpoints expand the attack surface and the test matrix without a consuming requirement. | N/A — deliberately out of scope. |
| 11 | Low | Suggested caching `calculate_price` with `functools.lru_cache`. | **Rejected** | The function is pure arithmetic costing nanoseconds; caching on unbounded `Decimal` inputs would add memory growth and risk without measurable benefit. | N/A — no change made. |

**Totals:** 11 findings — 7 accepted, 4 rejected.

## 5. Failure-Blocking Demonstration

To prove the pipeline gate is real, the discount rule was deliberately weakened
from `subtotal >= 1000` to `subtotal > 1000` in `app/pricing.py`.

**Result: 2 failed, 16 passed.** The boundary test caught it immediately:

```text
_______________ test_subtotal_exactly_at_threshold_gets_discount _______________
    assert Decimal(body["subtotal"]) == Decimal("1000.00")
>   assert body["discount_applied"] is True
E   assert False is True
tests/test_discount_rules.py:31: AssertionError

_______________ test_discount_boundary_matrix[1-1000.00-900.00] ________________
>   assert breakdown.total == Decimal(expected_total)
E   AssertionError: assert Decimal('1000.00') == Decimal('900.00')
E    + where Decimal('1000.00') = PriceBreakdown(subtotal=Decimal('1000.00'),
E        discount_applied=False, discount_amount=Decimal('0.00'),
E        total=Decimal('1000.00')).total

FAILED tests/test_discount_rules.py::test_subtotal_exactly_at_threshold_gets_discount
FAILED tests/test_discount_rules.py::test_discount_boundary_matrix[1-1000.00-900.00]
=================== 2 failed, 16 passed, 1 warning in 0.22s ====================
```

Pipeline behaviour on that run:

| Stage | Outcome |
|---|---|
| Build | Succeeded |
| Test | **Failed** — results and coverage still published (`condition: always()`) |
| Package | **Skipped** |
| Release Readiness | **Skipped** |
| Approval / Deploy | **Skipped** — approval never requested |
| Verify | **Skipped** |

The rule was then restored to `>=`, and the suite returned to **18 passed**,
allowing the run to proceed through `Verify`. This confirms both halves of the
gate: a broken boundary cannot reach production, and a correct one is not
impeded.

## 6. Artifact and Deployment Integrity

- `Package` produces exactly one versioned zip, `order-management-service-1.0.$(Build.BuildId).zip`, plus a SHA-256 checksum.
- `Deploy` downloads that artifact and runs `sha256sum -c` before deploying.
- `SCM_DO_BUILD_DURING_DEPLOYMENT=false` guarantees App Service does not rebuild; the deployed bits are byte-identical to the tested bits.
- Manual approval on the `production` environment gates the deployment job.

## 7. Verification

The `Verify` stage runs `tests/smoke/verify_deployment.py` against the live URL:
health contract, creation without discount, the 1000 boundary, retrieval, 404
handling and 422 validation. Evidence is published as the
`verification-evidence` artifact on both success and failure.

## 8. Known Limitations

- Storage is in-memory and process-local; orders do not survive restart or scale-out. Run on a single instance until persistence lands.
- No authentication or rate limiting. Intended to sit behind API Management or App Service authentication.

## 9. Reviewer Checklist

- [x] All acceptance criteria covered by automated tests
- [x] Boundary and failure paths tested
- [x] No secrets or credentials committed
- [x] Errors handled without leaking internals
- [x] Test results publish even on failure
- [x] Failed tests block downstream stages (demonstrated)
- [x] Deployed artifact is the tested artifact
- [x] README and release documentation updated
