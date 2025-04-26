# import debugpy

# # Allow other machines to attach if needed
# debugpy.listen(("0.0.0.0", 5678))
# print("⏳ Waiting for debugger attach...")

# # Pause the program until VS Code attaches
# debugpy.wait_for_client()
# print("✅ Debugger attached, continuing execution.")

import pulumi
import pulumi_aws as aws
from pulumi_aws import ec2

## --- Get the current AWS region
region = aws.get_region()
pulumi.export("region", region.name)

## --- Get list of all available Amazon AMI IDs in the current region 

## AWS CLI command
# aws ssm get-parameter \
#   --name /aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2 \
#   --query "Parameter.Value" \
#   --output text

## Approach #1
async def get_amazon_linux_amis():
    # Define the filters for Amazon Linux AMIs
    filters = [
        {"name": "name", "values": ["amzn2-ami-hvm-*"]},  # Filter for Amazon Linux AMIs
        {"name": "state", "values": ["available"]},  # Only available AMIs
        {"name": "root-device-type", "values": ["ebs"]}  # EBS-backed AMIs
    ]

    # Use the get_ami_ids function to get the list of AMI IDs
    result = await aws.ec2.get_ami_ids(
        filters=filters,
        owners=["amazon"],  # AMIs owned by Amazon
    )

    return result.ids

# Get the list of Amazon Linux AMIs and export it
ami_ids = pulumi.Output.from_input(get_amazon_linux_amis())
# ami_ids.apply(lambda ids: print("Amazon Linux AMI IDs:", ids))


## Approach #2
filters = [
        {
            "name": "name", 
            "values": ["amzn2-ami-hvm-*"]
        },  # Filter for Amazon Linux AMIs
        {
            "name": "state", 
            "values": ["available"]
        },  # Only available AMIs
        {
            "name": "root-device-type", 
            "values": ["ebs"]
        }  # EBS-backed AMIs
    ]
result = aws.ec2.get_ami_ids(
        filters=filters,
        owners=["amazon"],  # AMIs owned by Amazon
    )
# pulumi.export("Amazon Linux AMI IDs:", result.ids)




## --- Dynamically find the latest AMI
## Fetch the latest Amazon Linux 2 AMI
amazon_ami = aws.ec2.get_ami(
    most_recent=True,
    owners=["amazon"],
    filters=[
        {
            "name": "name", 
            "values": ["amzn2-ami-hvm-*"]
        },
        {
            "name": "virtualization-type", 
            "values": ["hvm"]
        }
    ]
)


## Fetch the latest Ubuntu AMI
ubuntu_ami = aws.ec2.get_ami_output(
    most_recent=True,
    owners=["099720109477"],
    filters=[
        {
            "name": "name",
            "values": ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"],
        },
        {
            "name": "virtualization-type",
            "values": ["hvm"],
        },
    ]
)

## Fetch the latest AMI assciated with the user account
# example = aws.ec2.get_ami(
#     executable_users=["self"],
#     most_recent=True,
#     name_regex="^myami-[0-9]{3}",
#     owners=["self"],
#     filters=[
#         {
#             "name": "name",
#             "values": ["myami-*"],
#         },
#         {
#             "name": "root-device-type",
#             "values": ["ebs"],
#         },
#         {
#             "name": "virtualization-type",
#             "values": ["hvm"],
#         },
#     ])


pulumi.export("ami_id", amazon_ami.id)
pulumi.export("ami_id_this", ubuntu_ami.id)



## Fetch an existing VPC
vpc = aws.ec2.get_vpc(
        default=True  # Example: just pick the default VPC
    )
pulumi.export("vpc_id", vpc.id)

## --- Create a security group
secgroup = ec2.SecurityGroup(
    'secgroup',
    description='Enable SSH access',
    ingress=[
        {
        'protocol': 'tcp', 
        'from_port': 22, 
        'to_port': 22, 
        'cidr_blocks': ['0.0.0.0/0'] # IP range that’s allowed — in this case, EVERYONE
        }
    ],
    egress=[{
            "protocol": "-1",
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": ["0.0.0.0/0"],
        }],
    )

# # Create an EC2 instance
instance = ec2.Instance(
    'my-instance',
    instance_type='t2.micro',
    security_groups=[secgroup.name],
    ami=amazon_ami.id,
    key_name='my-keypair' # The key_name refers to an SSH key pair that lets you safely log into your EC2 instance.
    )