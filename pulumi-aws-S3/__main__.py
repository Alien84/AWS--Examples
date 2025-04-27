import pulumi
from pulumi_aws import s3

# Create an S3 bucket
bucket = s3.Bucket('my-bucket',
    acl='private',
    tags={
        'Name': 'My bucket',
        'Environment': 'Development'
    },
    versioning={
        'enabled': True,
    },
    )

# Export the name of the bucket
pulumi.export('bucket_name', bucket.id)
