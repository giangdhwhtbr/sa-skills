# Architecture

## Summary

One region with two availability zones keeps booking running if a zone fails. Both views use the same groups: clients, edge, microservices, data, managed services and external systems. Only the public tier faces the internet; the data tier has no internet route.

## Decisions

- Managed services from the AWS profile for every logical component
- One region in the patients' home region and two availability zones
- The high-level and physical views share one layout (option shared-layout = true)

## Details

| Logical component | AWS service | Notes |
|---|---|---|
| api-gateway | Amazon API Gateway (HTTP API) | web and mobile routes; VPC Link to an internal load balancer |
| identity-provider | Amazon Cognito | patients in a user pool; staff federated from the corporate identity provider |
| message-broker | Amazon SNS FIFO + Amazon SQS FIFO | ordered per appointment; dead-letter queues |
| service-databases | Amazon Aurora PostgreSQL | one database per service |
| cache | Amazon ElastiCache (Redis) | slot availability cache |
| search-index | Amazon OpenSearch Service | clinic and doctor search |

| Tier | Internet route | Example range |
|---|---|---|
| public | true | 10.0.0.0/24 |
| app | false | 10.0.10.0/24 |
| data | false | 10.0.20.0/24 |

## Open questions

- None
