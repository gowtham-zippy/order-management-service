# Azure DevOps Work Items

Import-ready definitions for the Order Management Service capstone.
Replace `#XXX` / `#XX1`–`#XX8` with the real IDs assigned by Azure Boards.

---

## User Story #XXX — Order Management Service

**Work item type:** User Story
**Area path:** `OrderManagement\API`
**Iteration:** Sprint 1
**Story points:** 8
**Priority:** 1
**Tags:** `api; fastapi; pricing; cicd`

### Description

> **As a** sales operations user
> **I want** to submit an order and retrieve it later by its identifier
> **So that** order totals — including the volume discount — are calculated consistently and are auditable.

The service exposes a minimal HTTP API backed by in-memory storage. Pricing is
deterministic: `subtotal = quantity × unit_price`, with a 10% discount applied
when the subtotal reaches 1000.

### Acceptance Criteria

**AC1 — Create an order**
- **Given** a valid payload with `product_name`, `quantity` and `unit_price`
- **When** the client sends `POST /orders`
- **Then** the service responds `201 Created` with a unique `id`, the `subtotal`, `discount_applied`, `discount_amount`, `total` and `created_at`.

**AC2 — Subtotal below the threshold**
- **Given** an order whose subtotal is less than 1000 (e.g. qty 5 × 100 = 500)
- **When** the order is created
- **Then** `discount_applied` is `false`, `discount_amount` is `0.00` and `total` equals the subtotal (`500.00`).

**AC3 — Subtotal exactly at the threshold (boundary)**
- **Given** an order whose subtotal is exactly 1000 (e.g. qty 10 × 100)
- **When** the order is created
- **Then** `discount_applied` is `true`, `discount_amount` is `100.00` and `total` is `900.00`.
- *The boundary value is inclusive; this is the single most important rule in the story.*

**AC4 — Subtotal above the threshold**
- **Given** an order whose subtotal exceeds 1000 (e.g. qty 10 × 250 = 2500)
- **When** the order is created
- **Then** `discount_applied` is `true`, `discount_amount` is `250.00` and `total` is `2250.00`.

**AC5 — Validation**
- **Given** a payload with a missing or blank `product_name`, a `quantity` that is not greater than 0, or a `unit_price` that is not greater than 0
- **When** the client sends `POST /orders`
- **Then** the service responds `422 Unprocessable Entity` and the response identifies the offending field.

**AC6 — Retrieve an existing order**
- **Given** an order that was previously created
- **When** the client sends `GET /orders/{id}`
- **Then** the service responds `200 OK` with the identical stored representation.

**AC7 — Retrieve a missing order**
- **Given** an identifier that does not exist
- **When** the client sends `GET /orders/{id}`
- **Then** the service responds `404 Not Found` with a `detail` message naming the identifier, and no stack trace is leaked.

**AC8 — Health**
- **Given** the service is running
- **When** the client sends `GET /health`
- **Then** the service responds `200 OK` with `status: healthy`, the service name and the deployed version.

**AC9 — Monetary precision**
- All monetary values are computed with `Decimal` and rounded half-up to 2 decimal places; no binary floating-point drift is observable in responses.

**AC10 — Pipeline enforcement**
- A regression in the discount boundary rule causes the `Test` stage to fail, and the `Package`, `Deploy` and `Verify` stages do not run.

### Definition of Done
- [ ] All acceptance criteria demonstrably met by automated tests
- [ ] Code reviewed (human + AI review findings triaged)
- [ ] Unit test coverage >= 80%
- [ ] Multi-stage pipeline green end to end
- [ ] Release readiness report generated and approved
- [ ] Deployed to App Service and verification evidence published
- [ ] README updated

---

## Tasks

### Task #XX1 — Create FastAPI application skeleton and in-memory storage
**Parent:** #XXX · **Estimate:** 4h · **Activity:** Development

Scaffold a clean, layered project: `app/main.py` (app factory), `app/models.py`
(Pydantic request/response schemas), `app/storage.py` (thread-safe in-memory
repository), `app/routers/` (orders + health). Implement `POST /orders`,
`GET /orders/{id}` and `GET /health`. Add `requirements.txt`,
`requirements-dev.txt`, `.gitignore` and `pytest.ini`.

**Done when:** the app starts with `uvicorn app.main:app`, all three endpoints respond, and `/docs` renders the OpenAPI schema.

---

### Task #XX2 — Implement discount logic and total calculation
**Parent:** #XXX · **Estimate:** 3h · **Activity:** Development

Implement `app/pricing.py`: `subtotal = quantity × unit_price`; apply a 10%
discount when `subtotal >= 1000`. Use `Decimal` with `ROUND_HALF_UP` to 2 places.
Expose `subtotal`, `discount_applied`, `discount_amount` and `total` on the
response. Keep the threshold and rate as named constants.

**Done when:** AC2, AC3, AC4 and AC9 pass. The threshold is inclusive and covered by an explicit boundary test.

---

### Task #XX3 — AI-assisted (Copilot) code review and remediation
**Parent:** #XXX · **Estimate:** 2h · **Activity:** Development

Run a Copilot review over the pricing, storage, model and router modules. Record
every finding, the accept/reject decision, and the rationale. Apply accepted
remediations and re-run the suite.

**Done when:** `docs/pull-request.md` contains the full findings table with decisions, rationale and verification, and all accepted items are implemented.

---

### Task #XX4 — Author unit tests for all required scenarios
**Parent:** #XXX · **Estimate:** 4h · **Activity:** Testing

Cover: subtotal < 1000, subtotal == 1000, subtotal > 1000, invalid quantity,
invalid unit price, missing product name, existing order retrieval, missing
order retrieval, plus health. Emit JUnit XML and coverage XML.

**Done when:** the suite is green locally, coverage >= 80%, and results are consumable by `PublishTestResults@2`.

---

### Task #XX5 — Build the multi-stage CI/CD pipeline
**Parent:** #XXX · **Estimate:** 6h · **Activity:** Deployment

Author `azure-pipelines.yml` with stages Build → Test → Package → Release
Readiness → Approval → Deploy → Verify. Publish test results with `condition:
always()`. Fail the `Test` stage on any test failure so downstream stages are
skipped. Produce a versioned zip plus SHA-256 checksum. Factor reusable steps
into `pipelines/templates/`.

**Done when:** a passing run reaches `Verify`; a deliberately broken discount rule stops the run at `Test` with `Package`/`Deploy`/`Verify` skipped, while results still publish.

---

### Task #XX6 — Produce the release readiness report
**Parent:** #XXX · **Estimate:** 2h · **Activity:** Documentation

Create `docs/templates/release-readiness-report.md` covering quality gates,
scope, risk assessment, deployment plan, rollback plan, verification plan and
the GO/NO-GO decision. Render it in the pipeline with the real version, commit
and checksum substituted, and publish it as an artifact.

**Done when:** every successful run publishes a populated `release-readiness-report` artifact.

---

### Task #XX7 — Configure the approval gate and App Service deployment
**Parent:** #XXX · **Estimate:** 4h · **Activity:** Deployment

Create an agentless `Approval` stage using `ManualValidation@0` and the
`production` deployment environment. Implement
`pipelines/templates/deploy-appservice.yml` to zip-deploy the **downloaded**
artifact with `SCM_DO_BUILD_DURING_DEPLOYMENT=false`. Verify the artifact
checksum before deploying.

**Done when:** deployment cannot start before approval, deploys the identical artifact produced by `Package`, and performs no rebuild.

---

### Task #XX8 — Post-deployment verification and evidence
**Parent:** #XXX · **Estimate:** 3h · **Activity:** Testing

Implement `tests/smoke/verify_deployment.py` to assert health plus the live
order contract (creation, discount boundary, retrieval, 404, validation).
Render and publish `verification-evidence.md` and `results.json`.

**Done when:** the `Verify` stage fails the run on any failed check and publishes evidence on both success and failure.
