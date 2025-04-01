# prefixes are in fact creating folders to attach to path of an object

# create a bucket
aws s3 mb s3://my-bucket-aa01

# Create a folder
aws s3api put-object --bucket my-bucket--aa01 -key "hello/"

# Create many folder (The length of key can be 1024 byte)
aws s3api put-object --bucket my-bucket-aa01 --key "hello/buy/good/food/" --body="hello.txt"

aws s3api list-objects --bucket my-bucket-aa01

