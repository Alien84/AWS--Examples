resource "aws_s3_bucket" "my-bucket-aa01" {
  tags = {
    Name        = "My bucket"
    Environment = "Dev"
  }
}