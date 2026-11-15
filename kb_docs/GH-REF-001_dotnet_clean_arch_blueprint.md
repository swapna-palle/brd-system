---
source_id: GH-REF-001
source_type: org_standard
source_system: github
repo_name: corp-templates/dotnet8-clean-architecture
repo_url: https://internal.corp
authority: recommended
version: v2.3
---
## Solution Structure and Clean Architecture Layers
Reference Repo: `corp-templates/dotnet8-clean-architecture`.
Production .NET 8 solutions must enforce strict dependency inversion across four projects: `Domain` (entities, value objects, domain events, zero external NuGet dependencies), `Application` (CQRS commands/queries via MediatR, FluentValidation, interfaces), `Infrastructure` (EF Core 8, Npgsql, MassTransit, external adapters), and `Api` (ASP.NET Core endpoints, Entra ID auth, global `ProblemDetails` exception handler).

## Structured Observability with Serilog and OpenTelemetry
Reference Repo: `corp-templates/dotnet8-clean-architecture`.
All .NET services must configure `Serilog` emitting compact JSON logs to stdout enriched with `ApplicationName`, `Environment`, `TraceId`, and `SpanId` via OpenTelemetry (`OpenTelemetry.Extensions.Hosting`). Export OTLP traces and metrics to Azure Application Insights or Grafana Tempo.

## Database Migrations and Connection Resilience
Reference Repo: `corp-templates/dotnet8-clean-architecture`.
Configure `Npgsql` / EF Core with `EnableRetryOnFailure(maxRetryCount: 3)` and explicit connection pool limits. Schema changes must use forward-only EF Core Migrations generated via `dotnet ef migrations add` and reviewed in PRs; destructive column drops require a two-release expand-and-contract deployment.
