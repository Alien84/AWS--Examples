# Create a bucket
aws s3 mb s3://metadata-bucket-aa01


# Uploaf file with metadaa
aws s3api put-object --bucket metadata-bucket-aa01 --key myfile.txt --body myfile.txt --metadata Author=Ali

# Get metadata through head object
aws s3api head-object --bucket metadata-bucket-aa01 --key myfile.txt
