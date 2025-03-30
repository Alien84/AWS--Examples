# You can edit bucket ploicy without disabling Block public access. It can aslo be used instead of ACLs. 
# It's more flexible than acl. Read doumentation.
# We can set it to give access to other 

# Create a new bucket

aws s3api create-bucket --bucket test-mybucket-aa01 --regio eu-west-2 

# Create bucket policy to give access to a user from other aws account
# Edit policy.json, you need enter arn from other user account.
aws s3api put-bucket-policy --bucket amzn-s3-demo-bucket --policy file://policy.json

# In otger account, access the bucket
aws s3 cp myfile.txt s3://test-mybucket-aa01
aws s3 ls s3://test-mybucket-aa01