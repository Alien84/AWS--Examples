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

# Leys upload a file withh different type of checksum

sudo apt-get install rhash -y
rhash --crc32 --simple myfile.txt
# d620111a  myfile.txt


