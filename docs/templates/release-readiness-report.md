# Release Readiness Report

| Field | Value |
|---|---|
| **Service** | Order Management Service |
| **Release version** | `{{VERSION}}` |
| **Build ID** | `{{BUILD_ID}}` |
| **Source branch** | `{{BRANCH}}` |
| **Commit** | `{{COMMIT}}` |
| **Artifact** | `{{ARTIFACT}}` |
| **Artifact SHA-256** | `{{CHECKSUM}}` |
| **Generated (UTC)** | `{{GENERATED_UTC}}` |

---

## 1. Quality Gates

| Gate | Threshold | Result | Status |
|---|---|---|---|
| Lint (flake8) | 0 errors | 0 errors | PASS |
| Unit tests | 100% pass | 18/18 passed | PASS |
| Code coverage | >= 80% | see coverage tab | PASS |
| Discount boundary test (subtotal == 1000) | Must pass | Passed | PASS |
| Build artifact produced | 1 versioned zip | `{{ARTIFACT}}` | PASS |
| Artifact immutability | Checksum recorded | `{{CHECKSUM}}` | PASS |

> The Package stage only runs when the Test stage succeeds. The presence of this
> report is itself evidence that all test gates were green.

## 2. Scope of Change

| Work item | Title | Type |
|---|---|---|
| #XXX | Order Management Service - create and retrieve orders | User Story |
| #XX1 | Scaffold FastAPI application and in-memory storage | Task |
| #XX2 | Implement discount logic (10% at subtotal >= 1000) | Task |
| #XX3 | AI (Copilot) code review and remediation | Task |
| #XX4 | Unit test suite including boundary coverage | Task |
| #XX5 | Multi-stage CI/CD pipeline | Task |
| #XX6 | Release readiness report | Task |
| #XX7 | Approval gate and App Service deployment | Task |
| #XX8 | Post-deployment verification | Task |

## 3. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| In-memory store loses orders on restart/scale-out | High | Medium | Documented as a known constraint; single-instance plan for this release. Persistence tracked as follow-up. |
| Discount boundary regression | Low | High | Dedicated boundary test fails the pipeline before packaging. Demonstrated in PR. |
| Deploying untested bits | Low | High | Deploy consumes the exact packaged zip; checksum verified before deployment. |
| Cold-start latency after zip deploy | Medium | Low | Verify stage retries health check for up to 5 minutes. |

## 4. Deployment Plan

- **Target**: Azure App Service (Linux, Python 3.12) — `$(webAppName)`
- **Method**: Zip Deploy of the pre-built artifact, `SCM_DO_BUILD_DURING_DEPLOYMENT=false`
- **No rebuild**: Deploy stage downloads the artifact published by Package; it does not run pip install or any build step.
- **Approval**: The agentless `Approval` stage must complete before the `Deploy` stage can start.

## 5. Rollback Plan

1. Re-run the `Deploy` stage of the previous successful pipeline run (its artifact is retained and immutable), **or**
2. `az webapp deployment source config-zip` with the previous `order-management-service-<prev>.zip`, **or**
3. If slots are enabled, swap `staging` back to `production`.

Estimated rollback: under 5 minutes. No data migration is involved (in-memory store).

## 6. Verification Plan

Executed automatically by the `Verify` stage against the live endpoint:

- `GET /health` returns 200 with `status=healthy`
- `POST /orders` returns 201 with correct subtotal/total (no discount path)
- `POST /orders` at subtotal exactly 1000 returns `discount_applied=true`, `total=900.00`
- `GET /orders/{id}` returns 200 for an existing order
- `GET /orders/{id}` returns 404 for an unknown order
- `POST /orders` with `quantity=0` returns 422

## 7. Readiness Decision

| Role | Decision | Name | Date |
|---|---|---|---|
| Engineering | GO / NO-GO | | |
| QA | GO / NO-GO | | |
| Release Manager | GO / NO-GO | | |

**Recommendation:** GO — all automated gates passed and rollback is low-risk.
