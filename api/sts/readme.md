# Create a user with no permission
We need to create a new user with no permission and generate out access keys

aws iam create-user --user-name sts-machine-user

# Create a Role
We need to create a role that will access to a new resource via CloudFormation

# Use new user credntial and assume role