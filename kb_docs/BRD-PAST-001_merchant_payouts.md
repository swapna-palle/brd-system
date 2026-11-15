---
source_id: BRD-PAST-001
source_type: past_brd
chunk_mode: narrative
project: Enterprise Vendor Settlement Engine
complexity: high
outcome: delivered_on_time
---
## Business Objective & Scope
Automate daily settlement payouts for 15,000 enterprise vendors across 3 currencies using a .NET 8 settlement engine, replacing legacy SSIS batch jobs.

## Key Non-Functional Requirements
System must achieve 99.95% availability during settlement windows, guarantee exactly-once idempotent ledger entries, maintain p95 API latency under 250ms, and enforce Microsoft Entra ID RBAC with an immutable audit trail.

## Lessons & Architectural Outcome
Built on .NET 8 Clean Architecture with MassTransit Transactional Outbox over Azure Service Bus and PostgreSQL serializable transactions. Running a 2-week PoC in Phase 2 caught an external banking API throttling limit early.
