# Checksum
# A checksum is like a fingerprint for a file.
# When you create or download a file, a small code (the checksum) can be made from it using a special math formula. If even one tiny part of the file changes, the checksum will also change.

# ETag (Entity Tag)
# This is also like a fingerprint, but it’s used in web browsers (and web servers).
# Purpose:
# To know if a web page or file has changed since the last time you saw it
# Helps with browser caching


# Create a new s3 bucket
aws s3 mb s3://checksums-examples-aa-001

# Create a file that will do a checksum on
echo "Helll Mars" > myfile.txt

# Get a checksum of a file for md5
md5sum myfile.txt
# f396d45499a59bc651c17515dfd0f4fd  myfile.txt

# Upload our file to s3 and look at its etag
aws s3 cp myfile.txt s3://checksums-examples-aa-001
aws s3api head-object --bucket checksums-examples-aa-001 --key myfile.txt


# Lets upload a file withh different type of checksum

# Option 1: Using Python (boto3) with CRC32

# Option 2: Using aws cli
# Calculate CRC32 and encode in base64
crc32=$(python3 -c "import zlib; print('%08X' % (zlib.crc32(open('myfile.txt', 'rb').read()) & 0xFFFFFFFF
))")
crc32_b64=$(echo $crc32 | xxd -r -p | base64)

crc32_b64=$(echo "ibase=16; $crc32" | bc | awk '{printf "%08X", $1}' | xxd -r -p | base64)

# Upload with metadata
aws s3api put-object \
    --bucket checksums-examples-aa-001 \
    --key myfile.txt \
    --body myfile.txt \
    --metadata crc32=$crc32_b64

# To Verify After Upload
aws s3api head-object --bucket checksums-examples-aa-001 --key myfile.txt

# Change files and see how chechsums and etag change




