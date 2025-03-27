require 'aws-sdk-s3'
require 'pry'
require 'securerandom'

bucket_name = ENV['BUCKET_NAME']
region 'eu-west-2'
# puts bucket_name

client = Aws::S3::Client.new(
  #bregion: region_name,
  # credentials: credentials,
  # ...
)

resp = client.create_bucket({
  bucket: bucket_name, 
  create_bucket_configuration: {
    location_constraint: region, 
  }, 
})
binding.pry

number_of_files = 1 + rand(5)
puts "number_of_files: #{number_of_files}"

number_of_files.times.each do |i|
    puts "i: #{i}"
    filename = "file_#{i}.txt"
    output_path = "/tmp/#{filename}"

    File.open(output_path, "w") do |f|
        f.write(SecureRandom.uuid)
    end

    File.open(output_path, 'rb') do |f|
        s3.put_object(
            bucket: bucket_name,
            key: filename,
            body: f
        )
    end
end