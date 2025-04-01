# Create a new bucket

aws s3api create-bucket --bucket acl-mybucket-aa01 --region us-east-1 

# Turn off block public access for ACLs, default is false for all generated buckets
aws s3api put-public-access-block \
--bucket acl-mybucket-aa01 \
--public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Confirm by getting the metada
aws s3api get-public-access-block \
--bucket acl-mybucket-aa01

# Change bucket ownership and also checking aws console
aws s3api put-bucket-ownership-controls \
--bucket acl-mybucket-aa01 \
--ownership-controls="Rules=[{ObjectOwnership=BucketOwnerPreferred}]"

# Confirm by getting the metada and also checking aws console
aws s3api get-bucket-ownership-controls \
--bucket acl-mybucket-aa01

# Now you can edit ACL in console and users from other accounts to access s3 bucket. It's inactive without using that. 
# Grant access to another AWS account using ACL

aws s3api put-bucket-acl \
--bucket acl-mybucket-aa01 \
--access-control-policy '{
  "Grants": [
    {
      "Grantee": {
        "Type": "CanonicalUser",
        "ID": "OTHER_ACCOUNT_CANONICAL_ID"
      },
      "Permission": "FULL_CONTROL"
    }
  ],
  "Owner": {
    "ID": "YOUR_ACCOUNT_CANONICAL_ID"
  }
}'

# Or use this comman to load list from a json file
aws s3api put-bucket-acl \
--bucket acl-mybucket-aa01 \
--access-control-policy file://policy.json

# the next practice will be how you can access from the other account.
aws cp myfie.txt s3://acl-mybucket-aa01
aws s3 ls s3://acl-mybucket-aa01



# Cleanup
aws s3 rm s3://acl-mybucket-aa01/myfie.txt
aws s3 rb s3://acl-mybucket-aa01
