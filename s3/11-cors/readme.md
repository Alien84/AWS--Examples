# Create website 1

# Create a new bucket
aws s3api create-bucket --bucket test-mybucket-aa01 --region us-east-1 

# Change block public access
aws s3api put-public-access-block \
--bucket test-mybucket-aa01 \
--public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=false,RestrictPublicBuckets=false"

# Create a bucket policy: search for the static website bucket policy
aws s3api put-bucket-policy --bucket test-mybucket-aa01 --policy file://policy.json

# Turn on static website hosting
aws s3api put-bucket-website --bucket test-mybucket-aa01 --website-configuration file://website.json
# Check on console in Property section

# upload our index.html and include a resource that would be cross-origin
aws s3 cp index.html s3://test-mybucket-aa01

# Get website endpoint for s3
# You can take the link for the website using console/property
# View the website and see if the index.html is there

It this for ca-central-1
http://test-mybucket-aa01.s3-website.us-east-1.amazonaws.com/

or might be a . instead of -
http://test-mybucket-aa01-s3-website.us-east-1.amazonaws.com/



# Apply a CORS policy
