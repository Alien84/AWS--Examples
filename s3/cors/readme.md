# Create a new bucket

aws s3api create-bucket --bucket test-mybucket-aa01

# Change block public access
aws s3api put-public-access-block \
--bucket test-mybucket-aa01 \
--public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=false,RestrictPublicBuckets=false"

# Create a bucket policy

# Turn on static website hosting

# upload nourn index.html and include a resource that would be cross-origin

# Apply a CORS policy
