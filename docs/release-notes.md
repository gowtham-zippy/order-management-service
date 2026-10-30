# Release Notes — Order Management Service

## v1.0.0 — 2026-10-30

**Build:** `1.0.1428` · **Commit:** `a7f3c91` · **Environment:** Production (Azure App Service)
**Artifact:** `order-management-service-1.0.1428.zip`
**Approved by:** Release Manager · **Deployed:** 2026-10-30 14:22 UTC

### Overview

First production release of the Order Management Service. Provides order
creation and retrieval with deterministic volume-discount pricing, plus a
health endpoint for platform monitoring.

### New Features

| Work item | Description |
|---|---|
| #XXX | Order Management Service — create and retrieve orders |
| #XX1 | `POST /orders` creates an order and returns the full price breakdown |
| #XX1 | `GET /orders/{id}` retrieves a stored order |
| #XX1 | `GET /health` reports service status and deployed version |
| #XX2 | 10% volume discount applied when the subtotal reaches 1000 (inclusive) |
| #XX2 | `Decimal`-based monetary arithmetic, rounded half-up to 2 places |

### Business Rules

| Subtotal | Discount | Example |
|---|---|---|
| < 1000 | None | 5 × 100.00 → total **500.00** |
| = 1000 | 10% | 10 × 100.00 → total **900.00** |
| > 1000 | 10% | 10 × 250.00 → total **2250.00** |

### Validation

Requests are rejected with `422` when `product_name` is missing or blank,
`quantity` is not greater than 0, or `unit_price` is not greater than 0.
Unknown fields are rejected rather than silently ignored. Unknown order IDs
return `404` with a descriptive message.

### Engineering Changes

| Work item | Description |
|---|---|
| #XX3 | Copilot review completed — 11 findings, 7 accepted, 4 rejected |
| #XX4 | 18 unit tests; coverage above the 80% gate |
| #XX5 | Seven-stage pipeline with test-failure blocking and immutable artifacts |
| #XX6 | Automated release readiness report |
| #XX7 | Manual approval gate on the `production` environment |
| #XX8 | Automated post-deployment health and API verification |

### Quality Gates

| Gate | Result |
|---|---|
| Lint (flake8) | PASS — 0 issues |
| Unit tests | PASS — 18/18 |
| Coverage | PASS — above 80% threshold |
| Artifact checksum verified before deploy | PASS |
| Post-deployment verification | PASS — 6/6 checks |

### Known Limitations

- **In-memory storage.** Orders are held in process memory and are lost on restart or scale-out. Deploy on a single instance until persistence is delivered.
- **No authentication.** The API is unauthenticated; place it behind API Management or App Service authentication for external exposure.
- **Single-line orders.** One product per order; multi-line orders are not yet supported.

### Upgrade and Rollback

No migration is required — this is the initial release and no persistent state
exists. To roll back, re-run the `Deploy` stage of the previous successful
pipeline run or zip-deploy the previous artifact. Expected rollback under 5 minutes.

### Planned Next

- Durable persistence (Azure SQL or Cosmos DB)
- Multi-line orders
- Authentication and per-client rate limiting
- Configurable discount tiers

---

## Template for Future Releases

```markdown
## vX.Y.Z — YYYY-MM-DD

**Build:** `<build-number>` · **Commit:** `<sha>` · **Environment:** <env>
**Artifact:** `order-management-service-<version>.zip`
**Approved by:** <approver> · **Deployed:** <timestamp UTC>

### Overview
<one paragraph>

### New Features
| Work item | Description |

### Fixes
| Work item | Description |

### Quality Gates
| Gate | Result |

### Known Limitations

### Upgrade and Rollback
```
