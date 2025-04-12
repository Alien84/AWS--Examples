# Create a user with no permission
We need to create a new user with no permission and generate out access keys

aws iam create-user --user-name sts-machine-user
aws iam create-access-key --user-name sts-machine-user --output table

Copy the access key and secret here:
aws configure

Add sts to prfile in credential:
open ~/.aws/credentials

Test who you are:
aws sts get-caller-identity --profile 

Make sure this user don't have access to s3
aws s3 ls --profile sts

# Create a assume role
We need to create a role that will access to a new resource via CloudFormation

chmod u+x ./bin/deploy
./bin/deploy

# Use new user credntial and assume role

