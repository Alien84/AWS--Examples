# Create a user with no permission
We need to create a new user with no permission and generate out access keys

aws iam create-user --user-name sts-machine-user
aws iam create-access-key --user-name sts-machine-user --output table

Copy the access key and secret here:
aws configure 

Add sts to prfile in credential:
open ~/.aws/credentials

Test who you are:
aws sts get-caller-identity --profile sts

aws configure --profile sts

Make sure this user don't have access to s3
aws s3 ls --profile sts

# Create a assume role
We need to create a role that will access to a new resource via CloudFormation

chmod u+x ./bin/deploy
./bin/deploy

# Use new user credntial and assume role

aws iam put-user-policy \
    --user-name sts-machine-user \
    --policy-name StsAssumePolicy \
    --policy-document file://policy.json

aws sts assume-role \
    --role-arn arn:aws:iam::555576841436:role/cfn-sts-simple-StsRole-FTs3Fhp6OCzD \
    --role-session-name s3-sts-example \
    --profile sts

This will return temporary credentials:
{
    "Credentials": {
        "AccessKeyId": ,
        "SecretAccessKey": ,
        "SessionToken": 
    }
}

open ~/.aws/credentials and add this item as. a new profile:
[asumed]
aws_access_key_id = 
aws_secret_access_key = 
aws_session_token =

Test:
aws sts get-caller-identity --profile assumed

aws s3 ls s3://my-bucket-a03 --profile assumed
aws s3 ls --profile assumed

# Cleanup
aws iam delete-user-policy --user-name  sts-machine-user --policy-name StsAssumePolicy
aws iam delete-access-key --access-key-id AKIAYCWXV2TOPC7J4NYI --user-name  sts-machine-user
aws iam delete-user --user-name sts-machine-user 




