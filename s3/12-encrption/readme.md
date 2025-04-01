# Create a new bucket
aws s3 mb s3://enc-mybucket-aa02

# Put object with encryption of SS3-S3
aws s3 cp myfile.txt s3://enc-mybucket-aa02

# Put object with encryption of SSE-KMS
aws s3api put-object \
--bucket enc-mybucket-aa02 \
--key myfile.txt \
--body myfile.txt \
--server-side-encryption aws:kms

# Put object with encryption of SSE-C (Failed, try the second option)
export ENCODED_KEY=$(openssl rand -base64 32)
echo $ENCODED_KEY

export MD5_VALUE=$(echo -n $ENCODED_KEY | base64 --decode |cmd5sum | awk '{print $1}' | base64)
echo $MD5_VALUE

aws s3api put-object \
--bucket enc-mybucket-aa02 \
--key myfile.txt \
--body myfile.txt \
--sse-customer-algorithm AES256 \
--sse-customer-key $ENCODED_KEY \
--sse-customer-key-md5 $MD5_VALUE

openssl rand -out ssec.key 32
aws s3 cp myfile.txt s3://enc-mybucket-aa02/myfile.txt \
--sse-c AES256 \
--sse-c-key fileb://ssec.key

# Now, you cannot download the file without providing the key
aws s3 cp s3://enc-mybucket-aa02/myfile.txt myfile.txt --sse-c AES256 --sse-c-key fileb://ssec.key