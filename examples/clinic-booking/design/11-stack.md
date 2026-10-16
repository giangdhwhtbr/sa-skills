# Technology stack

## Summary

Managed AWS services for every layer keep the operations load small; one TypeScript team owns the clients and one Java team owns the services.

## Decisions

- Managed over self-run in every layer
- Java and Spring Boot for the services
- No second server-side runtime

## Details

| Layer | Choice | Reason |
|---|---|---|
| Clients | React and React Native with TypeScript | One team owns patient web, mobile and the staff portal |
| Edge | Route 53, CloudFront, WAF and API Gateway | Managed entry point with web and mobile routes |
| Services | Java and Spring Boot | Mature libraries for transactions, resilience and tracing, which the saga and outbox need |
| API contract | REST with OpenAPI; generated clients | Contract-first and tool-friendly |
| Messaging | SNS FIFO and SQS FIFO with dead-letter queues | Ordered per appointment; no brokers to run |
| Data | Aurora PostgreSQL per service, ElastiCache, OpenSearch, S3 | Transactions, cache, search and documents, all managed |
| Compute | ECS on Fargate with auto scaling | No cluster to operate; scales for the Monday peak |
| Observability | OpenTelemetry, X-Ray and CloudWatch | Managed tracing, metrics, logs and alarms |
| Security | Cognito, corporate identity federation, Secrets Manager | Zero trust with managed identity and secrets |

## Open questions

- None
