---
source_id: TPL-PLAN-001
source_type: plan_template
chunk_mode: narrative
template_type: agile_4_phase_dotnet
target_complexity: medium
---
## Phase 1: Discovery, Entra ID & Architecture Sign-Off (Weeks 1-2)
Deliverables: Threat model, OpenAPI 3.1 contract specs, EF Core / PostgreSQL schema design, Entra ID app registration, and Architecture Review Board (ARB) sign-off. Exit Criteria: Zero unresolved NFR ambiguities.

## Phase 2: Core .NET Foundation & PoC Validation (Weeks 3-4)
Deliverables: Azure DevOps CI/CD pipeline, `dotnet8-clean-architecture` solution scaffold, Entra ID JWT auth, and isolated PoC benchmark report. Exit Criteria: PoC latency and integration metrics validated.

## Phase 3: Feature Implementation & Integration (Weeks 5-8)
Deliverables: MediatR command/query handlers, MassTransit event consumers, external API adapters with Polly v8 resilience, and xUnit + Testcontainers integration suite. Exit Criteria: 80% test coverage and staging deployment complete.

## Phase 4: NFR Hardening, UAT & Production Cutover (Weeks 9-10)
Deliverables: Azure Load Testing / k6 report, Application Insights dashboards, operational runbooks, and blue-green production cutover. Exit Criteria: Sign-off from Engineering Manager and InfoSec.
