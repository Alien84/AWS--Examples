require 'aws-sdk-s3'
require 'openssl'
require 'pry'

key = OpenSSL::PKey::RSA.new(1024)

bucket = 'enc1-mybucket-aa02'
object_key = 'myfile.txt'

# encryption client
s3 = Aws::S3::EncryptionV2::Client.new(
  encryption_key: key,
  key_wrap_schema: :rsa_oaep_sha1, # the key_wrap_schema must be rsa_oaep_sha1 for asymmetric keys
  content_encryption_schema: :aes_gcm_no_padding,
  security_profile: :v2 # use :v2_and_legacy to allow reading/decrypting objects encrypted by the V1 encryption client
)

# round-trip an object, encrypted/decrypted locally
rep =s3.put_object(bucket:bucket, key:object_key, body:'handshake')
puts "PUT"
puts rep
rep = s3.get_object(bucket:bucket, key:object_key).body.read
puts "GET WITH KEY"
puts rep
#=> 'handshake'

# reading encrypted object without the encryption client
# results in the getting the cipher text
rep = Aws::S3::Client.new.get_object(bucket:bucket, key:object_key).body.read
puts "GET WITHOUT KEY"
puts rep
#=> "... cipher text ..."