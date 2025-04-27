"""AWS IAM: Managing Secure Access to AWS Resources with Pulumi"""

"""
This setup creates an IAM role that EC2 instances can assume, with permissions to perform actions on S3. 
The policy is defined inline, but you can also attach managed policies as shown.
"""

import pulumi
from pulumi_aws import iam

# Create an IAM role
role = iam.Role('my-role',
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }""")

# Attach a policy to the role
policy = iam.RolePolicy('my-policy',
    role=role.id,
    policy="""{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": "s3:*",
            "Resource": "*"
        }]
    }""")

# Optionally, you can use a managed policy
managed_policy_attachment = iam.RolePolicyAttachment('my-policy-attachment',
    role=role.id,
    policy_arn='arn:aws:iam::aws:policy/AmazonS3FullAccess')


"""
Consider implementing best practices such as:
- Least Privilege Principle: Always provide the minimum permissions necessary for the roles.
- Regular Audits and Reviews: Regularly review IAM roles and policies to ensure they remain secure and relevant.
- Use of Managed Policies: Where possible, use AWS managed policies for better maintenance and security.
"""