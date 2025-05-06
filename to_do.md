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



### Use Systems Manager (SSM) Instead

If you want secure access without any open SSH ports, consider switching to  **AWS Systems Manager (SSM) Session Manager** :

* No SSH needed
* No security group ingress rules
* Works via IAM + SSM agent installed on instance

Would you like me to show how to configure EC2 for SSM Session Manager access instead?
