# Order Management Service

A FastAPI service for creating and retrieving orders with automatic volume-discount
pricing, delivered with a seven-stage Azure DevOps pipeline.

[![Stages](https://img.shields.io/badge/pipeline-build%20%E2%86%92%20test%20%E2%86%92%20package%20%E2%86%92%20readiness%20%E2%86%92%20approval%20%E2%86%92%20deploy%20%E2%86%92%20verify-blue)]()

---

## Features

- `POST /orders` — create an order and receive the full price breakdown
- `GET /orders/{id}` — retrieve a stored order, with proper `404` handling
- `GET /health` — liveness and version probe
- 10% discount when the subtotal reaches **1000** (the boundary is inclusive)
- `Decimal` monetary arithmetic, rounded half-up to 2 decimal places
- Thread-safe in-memory storage
- 18 unit tests plus a live post-deployment verification suite

## Project Structure

```
order-management-service/
├── app/
│   ├── __init__.py              # package version
│   ├── main.py                  # FastAPI app factory
│   ├── models.py                # Pydantic request/response schemas
│   ├── pricing.py               # subtotal, discount and total calculation
│   ├── storage.py               # thread-safe in-memory repository
│   └── routers/
│       ├── health.py            # GET /health
│       └── orders.py            # POST /orders, GET /orders/{id}
├── tests/
│   ├── conftest.py              # TestClient fixture with per-test isolation
│   ├── test_discount_rules.py   # below / at / above the 1000 threshold
│   ├── test_validation.py       # quantity, unit_price, product_name
│   ├── test_orders_api.py       # retrieval, 404, health
│   └── smoke/
│       └── verify_deployment.py # live post-deployment verification
├── pipelines/templates/
│   ├── setup-python.yml
│   ├── deploy-appservice.yml    # zip-deploy, no rebuild
│   └── verify-deployment.yml    # health + API verification
├── infra/
│   └── main.bicep               # App Service plan + web app
├── docs/
│   ├── azure-devops-work-items.md
│   ├── pull-request.md
│   ├── commit-message.txt
│   ├── release-notes.md
│   └── templates/
│       ├── release-readiness-report.md
│       └── verification-evidence.md
├── .azuredevops/
│   └── pull_request_template.md
├── azure-pipelines.yml
├── startup.sh                   # gunicorn + uvicorn worker entry point
├── requirements.txt
├── requirements-dev.txt
└── pytest.ini
```

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

uvicorn app.main:app --reload
```

Interactive docs: <http://127.0.0.1:8000/docs>

## API Reference

### `POST /orders`

**Request**

```json
{
  "product_name": "Widget",
  "quantity": 10,
  "unit_price": 100.00
}
```

**Response — `201 Created`**

```json
{
  "id": "0f8a1c2e-5b7d-4a91-9c3e-2d6f8b4a1e70",
  "product_name": "Widget",
  "quantity": 10,
  "unit_price": "100.00",
  "subtotal": "1000.00",
  "discount_applied": true,
  "discount_amount": "100.00",
  "total": "900.00",
  "created_at": "2026-10-30T14:22:05.123456Z"
}
```

| Field | Rule |
|---|---|
| `product_name` | required, non-blank, 1–200 characters |
| `quantity` | integer, **> 0** |
| `unit_price` | decimal, **> 0** |

Unknown fields are rejected. Any violation returns `422` with the offending field named.

### `GET /orders/{id}`

`200 OK` with the stored order, or `404 Not Found`:

```json
{ "detail": "Order '00000000-0000-0000-0000-000000000000' not found" }
```

### `GET /health`

```json
{ "status": "healthy", "service": "order-management-service", "version": "1.0.0" }
```

## Business Rules

```
subtotal = quantity × unit_price

if subtotal >= 1000:
    discount = subtotal × 0.10
    total    = subtotal − discount
else:
    total    = subtotal
```

| Subtotal | Discount | Total |
|---|---|---|
| 500.00 | — | 500.00 |
| 999.99 | — | 999.99 |
| **1000.00** | **100.00** | **900.00** |
| 2500.00 | 250.00 | 2250.00 |

The threshold is **inclusive**. A subtotal of exactly 1000 qualifies — this is
enforced by a dedicated boundary test that blocks the pipeline if it regresses.

## Testing

```bash
pytest -v
pytest --cov=app --cov-report=term-missing
pytest --junitxml=test-results/junit.xml --cov=app --cov-report=xml
```

| Scenario | Test |
|---|---|
| Subtotal < 1000 | `test_subtotal_below_threshold_has_no_discount` |
| Subtotal = 1000 | `test_subtotal_exactly_at_threshold_gets_discount` |
| Subtotal > 1000 | `test_subtotal_above_threshold_gets_discount` |
| Invalid quantity | `test_invalid_quantity_is_rejected` |
| Invalid unit price | `test_invalid_unit_price_is_rejected` |
| Missing product name | `test_missing_product_name_is_rejected` |
| Blank product name | `test_blank_product_name_is_rejected` |
| Existing order retrieval | `test_existing_order_is_retrieved` |
| Missing order retrieval | `test_missing_order_returns_404` |
| Health | `test_health_endpoint` |

## CI/CD Pipeline

```
Build ─► Test ─► Package ─► Release Readiness ─► Approval ─► Deploy ─► Verify
          │                                          │
          │ results publish even on failure          │ manual gate
          └─► failure skips every downstream stage    on `production`
```

| Stage | Responsibility |
|---|---|
| **Build** | Install dependencies, lint (flake8), compile check, stamp the version |
| **Test** | Run pytest; publish JUnit + coverage with `condition: always()`; fail the stage on any test failure |
| **Package** | Vendor runtime dependencies, produce `order-management-service-<version>.zip` and its SHA-256 |
| **Release Readiness** | Render and publish the readiness report with real version, commit and checksum |
| **Approval + Deploy** | Manual approval on the `production` environment, then zip-deploy the downloaded artifact |
| **Verify** | Poll `/health`, exercise the live API contract, publish verification evidence |

### Guarantees

- **Results always publish.** The pytest step uses `continueOnError`, the publish tasks use `condition: always()`, and a subsequent gate step fails the stage. A red run is still fully diagnosable from the Tests tab.
- **Failures block.** `Package`, `ReleaseReadiness`, `Deploy` and `Verify` all carry `condition: succeeded()`, so a failing `Test` stage skips the rest of the run.
- **Artifacts are immutable and versioned.** One zip per build, named with the version and checksummed.
- **No rebuild on deploy.** `Deploy` downloads the artifact from `Package`, verifies its checksum, and deploys with `SCM_DO_BUILD_DURING_DEPLOYMENT=false`.

### One-time setup

1. **Variable group** `order-service-vars` (Pipelines → Library) containing:
   | Variable | Example |
   |---|---|
   | `azureSubscription` | `my-azure-service-connection` |
   | `webAppName` | `order-management-service` |
   | `resourceGroupName` | `rg-order-management` |
2. **Environment** `production` (Pipelines → Environments) with an **Approvals** check assigning the approver group.
3. **Service connection** — an Azure Resource Manager connection with Contributor on the resource group.

### Provision infrastructure

```bash
az group create --name rg-order-management --location eastus
az deployment group create \
  --resource-group rg-order-management \
  --template-file infra/main.bicep \
  --parameters webAppName=order-management-service
```

## Failure-Blocking Demonstration

Changing the rule in [app/pricing.py](app/pricing.py) from `subtotal >= DISCOUNT_THRESHOLD`
to `subtotal > DISCOUNT_THRESHOLD` produces:

```
FAILED tests/test_discount_rules.py::test_subtotal_exactly_at_threshold_gets_discount
FAILED tests/test_discount_rules.py::test_discount_boundary_matrix[1-1000.00-900.00]
=================== 2 failed, 16 passed, 1 warning in 0.22s ====================
```

The `Test` stage fails, results still publish, and `Package` / `Deploy` /
`Verify` are skipped. Restoring `>=` returns the suite to **18 passed** and the
run proceeds to `Verify`. Full evidence is in [docs/pull-request.md](docs/pull-request.md).

## Known Limitations

- **In-memory storage** — orders are process-local and lost on restart or scale-out. Run a single instance until persistence is added.
- **No authentication or rate limiting** — intended to sit behind API Management or App Service authentication.
- **Single-line orders** — one product per order.

## Documentation

| Document | Purpose |
|---|---|
| [docs/azure-devops-work-items.md](docs/azure-devops-work-items.md) | User story with acceptance criteria and the eight tasks |
| [docs/pull-request.md](docs/pull-request.md) | Completed PR description with Copilot review findings and decisions |
| [docs/commit-message.txt](docs/commit-message.txt) | Commit message with work-item references |
| [docs/release-notes.md](docs/release-notes.md) | Sample release notes and reusable template |
| [docs/templates/release-readiness-report.md](docs/templates/release-readiness-report.md) | Readiness report rendered by the pipeline |
| [docs/templates/verification-evidence.md](docs/templates/verification-evidence.md) | Verification evidence rendered by the pipeline |
| [.azuredevops/pull_request_template.md](.azuredevops/pull_request_template.md) | Blank PR template for future changes |
