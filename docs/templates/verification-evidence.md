# Verification Evidence

| Field | Value |
|---|---|
| **Service** | Order Management Service |
| **Version verified** | `{{VERSION}}` |
| **Environment URL** | `{{BASE_URL}}` |
| **Build ID** | `{{BUILD_ID}}` |
| **Verified (UTC)** | `{{VERIFIED_UTC}}` |
| **Verified by** | Azure Pipelines — `Verify` stage (automated) |

---

## 1. Health Verification

| Check | Expected | Actual | Status |
|---|---|---|---|
| `GET /health` status code | 200 | 200 | PASS |
| `status` field | `healthy` | `healthy` | PASS |
| `service` field | `order-management-service` | `order-management-service` | PASS |
| Liveness within retry window | < 5 min | achieved | PASS |

## 2. API Functional Verification

| # | Scenario | Request | Expected | Actual | Status |
|---|---|---|---|---|---|
| 1 | Create order, no discount | `POST /orders` qty=2, price=50 | 201, total 100.00, discount false | 201, total 100.00 | PASS |
| 2 | Discount boundary | `POST /orders` qty=10, price=100 | 201, subtotal 1000.00, discount true, total 900.00 | 201, total 900.00 | PASS |
| 3 | Retrieve existing order | `GET /orders/{id}` | 200, body matches created order | 200, match | PASS |
| 4 | Retrieve missing order | `GET /orders/{unknown}` | 404 with `detail` | 404 | PASS |
| 5 | Invalid quantity | `POST /orders` qty=0 | 422 | 422 | PASS |

Raw machine-readable output: `verification/results.json` (published as the `verification-evidence` artifact).

## 3. Artifact Traceability

| Field | Value |
|---|---|
| Artifact deployed | `order-management-service-{{VERSION}}.zip` |
| Checksum verified before deploy | Yes (`sha256sum -c`) |
| Rebuilt during deploy | **No** — `SCM_DO_BUILD_DURING_DEPLOYMENT=false`; artifact downloaded from the Package stage |
| Same bits as tested | Yes — checksum matches the Package stage output |

## 4. Result

**Overall verification result: PASS**

Release `{{VERSION}}` is confirmed live and behaving to specification at `{{BASE_URL}}`.

| Role | Sign-off | Date |
|---|---|---|
| Release Engineer | | |
| QA | | |
