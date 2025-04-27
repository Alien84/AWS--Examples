"""Amazon DynamoDB: Deploying a NoSQL Database with Pulumi"""

"""Amazon DynamoDB is a fast and flexible NoSQL database service for all applications that need consistent, single-digit millisecond latency at any scale. 
It is a fully managed, serverless database that supports both document and key-value store models. 
This chapter will guide you through setting up a DynamoDB table using Pulumi to manage infrastructure through code efficiently and reliably."""

import pulumi
from pulumi_aws import dynamodb

# Create a DynamoDB table
dynamodb_table = dynamodb.Table('my-table',
    attributes=[
        {"name": "Id", "type": "S"},
        {"name": "Data", "type": "S"}
    ],
    hash_key="Id",
    range_key="Data",
    billing_mode="PAY_PER_REQUEST",
    tags={
        "Environment": "Development"
    })

"""
Consider implementing additional configurations such as:
- Secondary Indexes: For enhancing query performance with alternative key structures.
- Stream Settings: Enable DynamoDB Streams if you need to capture changes to items on your table in near real time.
- Auto Scaling: Although not needed with pay-per-request, for other billing modes, set up auto-scaling on your table to manage throughput capacity based on actual usage.
"""
