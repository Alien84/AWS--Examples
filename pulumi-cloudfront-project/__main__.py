"""Amazon CloudFront: Setting Up a Content Delivery Network with Pulumi"""
"""
Amazon CloudFront is a fast content delivery network (CDN) service that securely 
delivers data, videos, applications, and APIs to customers globally with low latency 
and high transfer speeds. Using Pulumi to manage CloudFront distributions allows you 
to automate the setup and configuration of your CDN, ensuring consistent deployment across environments.
"""

import pulumi
from pulumi_aws import s3, cloudfront
import json

# Create an S3 bucket for website content
bucket = s3.Bucket('my-bucket',
    website={
        'index_document': 'index.html'
    })

# Upload an example file to the bucket
index_content = s3.BucketObject('index.html',
    bucket=bucket.id,
    content='<html><body><h1>Hello, World!</h1></body></html>',
    content_type='text/html')

# Create an OAI (Origin Access Identity) for CloudFront
oai = cloudfront.OriginAccessIdentity('my-oai')

# Grant the OAI access to the bucket
bucket_policy = s3.BucketPolicy('bucket-policy',
    bucket=bucket.id,
    policy=pulumi.Output.all(bucket.arn, oai.iam_arn).apply(lambda args: json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
                "AWS": args[1]  # oai.iam_arn
            },
            "Action": "s3:GetObject",
            "Resource": f"{args[0]}/*"  # bucket.arn
        }]
    }))
)


# Create a CloudFront distribution
distribution = cloudfront.Distribution('my-distribution',
    origins=[{
        'domain_name': bucket.bucket_regional_domain_name,
        'origin_id': 'my-origin',
        's3_origin_config': {
            'origin_access_identity': oai.cloudfront_access_identity_path
        },
    }],
    enabled=True,
    default_cache_behavior={
        'viewer_protocol_policy': 'redirect-to-https',
        'allowed_methods': ['GET', 'HEAD'],
        'cached_methods': ['GET', 'HEAD'],
        'target_origin_id': 'my-origin',
        'forwarded_values': {
            'query_string': False,
            'cookies': {'forward': 'none'},
        },
        'min_ttl': 0,
        'default_ttl': 3600,
        'max_ttl': 86400,
    },
    default_root_object='index.html',
    price_class='PriceClass_All',
    viewer_certificate={'cloudfront_default_certificate': True},
    restrictions={
        'geo_restriction': {
            'restriction_type': 'none'
        }
    },
    )

# Export the distribution's URL
pulumi.export('cloudfront_url', distribution.domain_name.apply(lambda domain: f"https://{domain}"))

"""
- Navigate to the provided CloudFront URL in your web browser to see the “Hello, World!” message served through the CDN.
- Test the distribution’s performance and caching behavior via tools like CDNPerf or WebPageTest.
"""
"""
Setting up Amazon CloudFront with Pulumi allows for an automated, reproducible method of deploying a CDN. 
This example covers serving static content from an S3 bucket, but CloudFront’s capabilities extend to dynamic content, 
streaming, and custom origin configurations, providing a robust solution for your content delivery needs.
"""