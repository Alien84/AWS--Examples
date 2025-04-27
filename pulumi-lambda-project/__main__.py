import pulumi
from pulumi_aws import iam, lambda_

# Create IAM Role for the Lambda function
role = iam.Role('lambda-role',
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Effect": "Allow",
            "Sid": ""
        }]
    }""")

# Attach the AWS Lambda Basic Execution Role policy
policy_attachment = iam.RolePolicyAttachment('lambda-policy-attachment',
    role=role.name,
    policy_arn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole')

# Create the Lambda function
lambda_function = lambda_.Function('my-lambda-function',
    role=role.arn,
    runtime='python3.8',
    handler='lambda_function.handler',
    code=pulumi.FileArchive('./lambda_code'))

# Define the handler code directory
# Note: Ensure there's a lambda_function.py file with a 'handler' function

"""
Step 4: Test Your Lambda Function
- Once deployed, you can invoke your Lambda function directly from the AWS Management Console, AWS CLI, or through an event source such as an S3 bucket or an API Gateway.
"""