"""AWS CloudTrail: Monitoring AWS Account Activity with Pulumi"""

"""
AWS CloudTrail is a service that enables governance, compliance, operational auditing, and risk auditing of your AWS account. 
With CloudTrail, you can log, continuously monitor, and retain account activity related to actions across your AWS infrastructure.
"""

import pulumi
from pulumi_aws import cloudtrail, s3

""""
This script sets up an AWS CloudTrail that logs events across all regions to an S3 bucket. 
The trail is configured to include global service events, which means events from AWS services that are not region-specific will also be logged.
"""
# Create an S3 bucket to store the CloudTrail logs
log_bucket = s3.Bucket('cloudtrail-log-bucket')

# Create a CloudTrail
trail = cloudtrail.Trail('my-trail',
    s3_bucket_name=log_bucket.id,
    include_global_service_events=True,
    is_multi_region_trail=True,
    enable_logging=True)

# Export the name of the bucket and the trail ARN
pulumi.export('log_bucket_name', log_bucket.id)
pulumi.export('trail_arn', trail.arn)

"""
Best Practices and Additional Configurations
Consider implementing best practices such as:
- Log File Validation: Enable log file validation to ensure the integrity of your logs.
- Log Encryption: Use AWS KMS to encrypt your log files stored in S3.
- Fine-Grained Access Control: Manage access to your CloudTrail logs using IAM policies and S3 bucket policies.
"""