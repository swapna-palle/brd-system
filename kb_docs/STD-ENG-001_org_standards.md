---
source_id: STD-ENG-001
source_type: org_standard
source_system: confluence
confluence_space: ENG-STANDARDS
page_url: https://internal.corp
authority: mandatory
version: v4.2
---
## Approved Languages and .NET Runtime Standards
All new backend microservices and APIs must be built on .NET 8 LTS (C# 12) using ASP.NET Core Minimal APIs or Web API controllers. Python is restricted strictly to isolated AI/ML data pipelines. Frontend enterprise portals must use React with TypeScript or Blazor Server/WebAssembly for internal line-of-business tools.

## Approved Data, Caching, and Messaging Stores
PostgreSQL 16+ (with Npgsql and pgvector for AI workloads under 5M vectors) or Azure SQL Database are the mandatory primary relational datastores. Redis Enterprise (StackExchange.Redis) is mandatory for distributed caching. Azure Service Bus or RabbitMQ (via MassTransit) is mandatory for asynchronous event-driven messaging.

## Security, Identity, and Compliance Standards
All APIs and web portals must authenticate via Microsoft Entra ID (Azure AD) using OAuth 2.0 / OpenID Connect and JWT bearer validation. Secrets must be stored in Azure Key Vault (never in appsettings.json). All database access must use parameterized queries via EF Core 8 or Dapper, and logs must hash sensitive BRD/PII payloads with SHA-256.

## CI/CD and Quality Gates
All repositories must run on Azure DevOps Pipelines or GitHub Actions with `dotnet test` enforcing a minimum 80% unit/integration test coverage (xUnit + Testcontainers), SonarQube static analysis gates, and zero-downtime blue-green deployments on Azure App Service or AKS.
