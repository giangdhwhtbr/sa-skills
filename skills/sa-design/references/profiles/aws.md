# Cloud profile: AWS

Used from step 10 (architecture) and step 11 (stack) when `cloud: aws` in `design/sa-config.yaml`. Each row maps a logical component kind from `logical.yaml` to the default AWS service and the notes a reviewer usually asks about. Deviate only for a constraint in the brief, and record the reason in the mapping notes.

| kind | AWS service | notes |
|---|---|---|
| edge | Route 53, CloudFront, AWS WAF | DNS, CDN and web firewall in front of the gateway |
| gateway | Amazon API Gateway (HTTP API) | separate web and mobile route sets (backend-for-frontend); JWT authorizer; VPC Link to an internal Application Load Balancer |
| identity-provider | Amazon Cognito | travelers or customers in a user pool; staff through a federated corporate identity provider |
| service | Amazon ECS on AWS Fargate | stateless tasks in private app subnets in two zones; auto scaling; Service Connect for service-to-service calls |
| broker | Amazon SNS FIFO + Amazon SQS FIFO | ordered per business key; dead-letter queues; Amazon EventBridge Scheduler for timed jobs |
| datastore | Amazon Aurora PostgreSQL, Amazon ElastiCache (Redis), Amazon OpenSearch Service, Amazon S3 | database per service (own schema or cluster); writer and reader in different zones |
| observability | Amazon CloudWatch, AWS X-Ray via AWS Distro for OpenTelemetry | metrics, logs, alarms and traces |
| secrets | AWS Secrets Manager, AWS KMS | database credentials and API keys; encryption keys |
| ai | Amazon Bedrock | managed models; agents get read-only tools |
| delivery | Amazon ECR, CI/CD runner of the team's choice | images built once and promoted; rolling deploy to ECS |

## Default network

- One region, two availability zones.
- Subnet tiers per zone: public (NAT gateway, internet gateway route), app (Fargate tasks, outbound through NAT only), data (Aurora, ElastiCache, OpenSearch; no internet route).
- Security groups: the load balancer accepts only the VPC Link, tasks only the load balancer, databases only the tasks.
- VPC endpoints for SNS, SQS, S3, Secrets Manager, ECR, CloudWatch and Bedrock, so traffic to AWS services stays private.
- Site-to-Site VPN for on-premises systems.

## Default stack notes

- Compute: ECS on Fargate rather than EKS when the team does not need Kubernetes features; no cluster to operate.
- Messaging: SNS FIFO + SQS FIFO rather than Amazon MSK (Kafka) when ordering per key and at-least-once delivery are enough.
- Gateway: HTTP API rather than REST API type unless request transformation or usage plans are needed.
