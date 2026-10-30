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
| `GET /health` status code | 200 | See `results.json` | See `results.json` |
| `status` field | `healthy` | See `results.json` | See `results.json` |
| `service` field | `order-management-service` | See `results.json` | See `results.json` |
| `version` field | `{{VERSION}}` | See `results.json` | See `results.json` |

## 2. API Functional Verification

| # | Scenario | Request | Expected | Actual | Status |
|---|---|---|---|---|---|
| 1 | Create order, no discount | `POST /orders` qty=2, price=50 | 201, total 100.00, discount false | See `results.json` | See `results.json` |
| 2 | Discount boundary | `POST /orders` qty=10, price=100 | 201, subtotal 1000.00, discount true, total 900.00 | See `results.json` | See `results.json` |
| 3 | Retrieve existing order | `GET /orders/{id}` | 200, body matches created order | See `results.json` | See `results.json` |
| 4 | Retrieve missing order | `GET /orders/{unknown}` | 404 with `detail` | See `results.json` | See `results.json` |
| 5 | Invalid quantity | `POST /orders` qty=0 | 422 | See `results.json` | See `results.json` |

Raw machine-readable output: `verification/results.json` (published as the `verification-evidence` artifact).

## 3. Artifact Traceability

| Field | Value |
|---|---|
| Artifact deployed | `order-management-service-{{VERSION}}.zip` |
| Checksum verified before deploy | Yes (`sha256sum -c`) |
| Rebuilt during deploy | **No** — `SCM_DO_BUILD_DURING_DEPLOYMENT=false`; artifact downloaded from the Package stage |
| Same bits as tested | Yes — checksum matches the Package stage output |

## 4. Result

**Overall verification result: {{OVERALL_RESULT}}**

Machine-readable check details are recorded in `results.json` for release
`{{VERSION}}` at `{{BASE_URL}}`.

| Role | Sign-off | Date |
|---|---|---|
| Release Engineer | | |
| QA | | |
