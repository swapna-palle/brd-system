---
source_id: CONF-CODE-001
source_type: org_standard
source_system: confluence
confluence_space: ENG-ARCH
page_url: https://internal.corp
authority: mandatory
version: v3.5
---
## Transactional Outbox Pattern with MassTransit and EF Core
Source: Confluence Space ENG-ARCH | Last Updated: 2026-09-10.
When a .NET service updates PostgreSQL/Azure SQL state and publishes a domain event to Azure Service Bus, never perform dual writes without a transaction boundary. Configure MassTransit's Entity Framework Core Transactional Outbox (`AddEntityFrameworkOutbox<AppDbContext>`) so domain entities and outbox messages commit in the same ACID transaction before background delivery.

## Resilience Pipelines with Polly v8 (.NET Standard Resilience)
Source: Confluence Space ENG-ARCH | Last Updated: 2026-09-18.
All outbound `HttpClient` calls to external partner APIs or AI gateways must register `AddStandardResilienceHandler()` via `Microsoft.Extensions.Http.Resilience` (Polly v8). Enforce a 5-second connection timeout, 30-second total request timeout, 3 retries with exponential backoff and jitter on HTTP 429/502/503, and a circuit breaker opening at 50% failure rate.

## Idempotency Filter Pattern for ASP.NET Core APIs
Source: Confluence Space ENG-ARCH | Last Updated: 2026-10-01.
All state-mutating POST/PUT endpoints (such as payouts, orders, or approvals) must apply an `IdempotencyEndpointFilter` validating the `X-Idempotency-Key` header (GUID). Store the key, SHA-256 request payload hash, and serialized HTTP response in Redis with a 24-hour TTL; return HTTP 422 if the same key is reused with a different payload.
