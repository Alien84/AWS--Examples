SG

* How to **use Pulumi Config** for ports and CIDRs.
* How to  **separate private vs public rules** .
* How to **combine security groups** (e.g., web + db SG).

System Design

| **Add a domain name** | Easier access (e.g.,`chat.example.com`) | Use Route 53 or your domain provider |
| --------------------------- | ----------------------------------------- | ------------------------------------ |

| **Set up HTTPS** | Secure your app traffic | Certbot + NGINX |
| ---------------------- | ----------------------- | --------------- |

| **Use a database** | For more real-world apps | Postgres, DynamoDB, etc. |
| ------------------------ | ------------------------ | ------------------------ |

| **Create an AMI image** | Backup your current server | AWS Console > Create AMI |
| ----------------------------- | -------------------------- | ------------------------ |

| **Scale later** | Handle more traffic | EC2 Auto Scaling or ECS/Fargate |
| --------------------- | ------------------- | ------------------------------- |

| **Monitoring and alerting** | Detect crashes, CPU spikes | AWS CloudWatch |
| --------------------------------- | -------------------------- | -------------- |



### 5.2 Advanced Options and Optimizations

**Goal:** Explore advanced AWS services and optimizations for your application.

**Why This Matters:** Understanding advanced options helps you make informed decisions as your application grows.

**How:**

Here are some advanced improvements to consider:

1. **Containerization:**
   * Move from EC2 to ECS (Elastic Container Service) or EKS (Elastic Kubernetes Service)
   * Benefits: improved resource utilization, faster deployments, better isolation
2. **API Gateway and Lambda:**
   * Use API Gateway for API management
   * Implement serverless functions with Lambda
   * Benefits: reduced operational complexity, automatic scaling, pay-per-use pricing
3. **Enhanced Security:**
   * Implement AWS WAF for web application firewall protection
   * Use AWS Shield for DDoS protection
   * Set up AWS Config for compliance monitoring
   * Implement AWS GuardDuty for threat detection
4. **Improved Database Options:**
   * Consider Amazon Aurora for better performance and availability
   * Implement read replicas for read-heavy workloads
   * Use DynamoDB for NoSQL requirements
   * Implement database caching with ElastiCache
5. **Content Delivery and DNS:**
   * Use CloudFront for content delivery
   * Set up Route 53 for DNS management
   * Configure custom domain names and SSL certificates
6. **Advanced Monitoring:**
   * Implement AWS X-Ray for distributed tracing
   * Use AWS CloudTrail for API auditing
   * Set up Prometheus and Grafana for enhanced monitoring
7. **Disaster Recovery:**
   * Implement multi-region deployments
   * Set up cross-region replication for S3 and databases
   * Create disaster recovery runbooks
