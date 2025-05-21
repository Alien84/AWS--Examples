import json
import hashlib
import pulumi
import pulumi_aws as aws
import pulumi_tls as tls
import base64
from ec2_instance import create_ec2_instance
from vpc import create_vpc
from rds import create_rds_instance
from secrets import create_secrets_with_kms, create_ssm_secrets

# Configuration
config = pulumi.Config()
key_name = config.get("keyName")
instance_type = config.get("instanceType") or "t2.micro"
auto_scaling = False

# Generate a private key
private_key = tls.PrivateKey("chatbot-private-key",
    algorithm="RSA",
    rsa_bits=4096
)

key_pair = aws.ec2.KeyPair("chatbot-keypair", 
    key_name="chatbot-keypair",
    public_key=private_key.public_key_openssh,
    tags={"Name": "chatbot-keypair"}
)

# Steps after deployment
# 1. Download the private key from AWS console
# 2. Save it to a file named "chatbot-keypair.pem"
# 3. Change permissions: chmod 400 chatbot-keypair.pem
# 4. SSH into the instance: ssh -i chatbot-keypair.pem ec2-user@<instance-public-ip>
# pulumi stack output private_key_pem --show-secrets > chatbot-keypair.pem
# chmod 400 chatbot-keypair.pem



pulumi.export("private_key_id", key_pair.key_pair_id)
pulumi.export("private_key_pem", private_key.private_key_pem)

# Read the user data script
with open("user_data.sh", "r") as f:
    user_data_template = f.read()


# Create VPC and networking components
network = create_vpc("chatbot")

# Create a security group for app server within the VPC
web_sg = aws.ec2.SecurityGroup(
    "web-sg",
    vpc_id=network["vpc"].id,
    description="Allow web traffic",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"],
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=443,
            to_port=443,
            cidr_blocks=["0.0.0.0/0"],
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr_blocks=["0.0.0.0/0"],  # In production, restrict this
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
)

# Create a security group for db within the VPC
db_sg = aws.ec2.SecurityGroup(
    "db-sg",
    vpc_id=network["vpc"].id,
    description="Allow database traffic",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=5432,  # PostgreSQL port
            to_port=5432,
            security_groups=[web_sg.id],  # Only allow access from web servers
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    tags={"Name": "chatbot-db-sg"},
)



# Create the RDS instance
database = create_rds_instance(
    "chatbot",
    network["vpc"].id,
    # [subnet.id for subnet in network["private_subnets"]],
    [subnet.id for subnet in network["public_subnets"]],
    [db_sg.id],
)

# Create secrets for database credentials
# NOTE -- Method #1: Apply the user data script with database credentials directly
# user_data = pulumi.Output.all(
#     database["instance"].endpoint,
#     database["username"],
#     database["password"],
#     database["database"]
# ).apply(
#     lambda args: user_data_template.replace("DB_HOST_PLACEHOLDER", args[0].split(':')[0])
#                           .replace("DB_PORT_PLACEHOLDER", args[0].split(':')[1])
#                           .replace("DB_NAME_PLACEHOLDER", args[3])
#                           .replace("DB_USER_PLACEHOLDER", args[1])
#                           .replace("DB_PASS_PLACEHOLDER", args[2])
# )


# NOTE -- Method #2: Using AWS Secrets Manager (NOTE this is not free)
# db_secrets = create_secrets_with_kms(
#     "chatbot-db-credentials",
#     {
#         "username": database["username"],
#         "password": database["password"],
#         "host": database["instance"].address,
#         "port": database["instance"].port,
#         "dbname": database["database"],
#     },
# )
# # Export the secret name for reference
# pulumi.export("db_secret_name", db_secrets["secret"].name)

# Process the user data script with environment variables
# user_data = pulumi.Output.all(db_secrets["secret"].name).apply(
#     lambda args: user_data_template.replace("${DB_SECRET_NAME}", args[0])
# )

# Create secrets for database credentials using ssm
# NOTE -- Method #3: Using AWS SSM Parameter Store (Standard tier is free)
db_secrets = create_ssm_secrets(
    "db",
    {
        "username": database["username"],
        "password": database["password"],
        "host": database["instance"].address,
        "port": database["instance"].port.apply(lambda p: str(p)),
        "dbname": database["database"],
    },
)

# Export the secret name for reference
pulumi.export("db_param_path", "/chatbot/db")

user_data = user_data_template.replace("${DB_PARAM_PATH}", "/chatbot/db")


# Create an IAM role for EC2 instances
ec2_role = aws.iam.Role(
    "ec2-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com",
            },
        }],
    }),
)

# NOTE Create a policy for Secrets Manager access
# secrets_policy = aws.iam.Policy(
#     "secrets-policy",
#     policy=pulumi.Output.all(db_secrets["secret"].arn).apply(
#         lambda args: json.dumps({
#             "Version": "2012-10-17",
#             "Statement": [{
#                 "Effect": "Allow",
#                 "Action": [
#                     "secretsmanager:GetSecretValue",
#                     "secretsmanager:DescribeSecret",
#                 ],
#                 "Resource": args[0],
#             }],
#         })
#     ),
# )


# NOTE Create a policy for SSM Parameter Store access instead of Secrets Manager
secrets_policy = aws.iam.Policy(
    "ssm-policy",
    policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter",
                "ssm:GetParameters",
                "ssm:GetParametersByPath",
            ],
            "Resource": [
                "arn:aws:ssm:eu-west-2:555576841436:parameter/chatbot/db",
                "arn:aws:ssm:eu-west-2:555576841436:parameter/chatbot/db/*",
            ],
        }],
    }),
)

# Attach the policy to the role
role_policy_attachment = aws.iam.RolePolicyAttachment(
    "role-policy-attachment",
    role=ec2_role.name,
    policy_arn=secrets_policy.arn,
)

# Create an instance profile
instance_profile = aws.iam.InstanceProfile(
    "instance-profile",
    role=ec2_role.name,
)


# Create an EC2 instance using default vpc
# instance, security_group = create_ec2_instance(
#     "chatbot-server",
#     instance_type=instance_type,
#     key_name=key_pair.key_name,
#     user_data=user_data,
# )

# Generate a hash of the user_data to trigger changes
user_data_hash = hashlib.sha256(user_data.encode('utf-8')).hexdigest()

if not auto_scaling:
    # Single instance creation:  Uncomment out if you comment out auto-scaling part

    # Create an EC2 instance in a public subnet
    instance = aws.ec2.Instance(
        "chatbot-server",
        instance_type=instance_type,
        ami=aws.ec2.get_ami(
            most_recent=True,
            owners=["amazon"],
            filters=[
                aws.ec2.GetAmiFilterArgs(
                    name="name",
                    values=["amzn2-ami-hvm-*-x86_64-gp2"],
                ),
            ],
        ).id,
        key_name=key_pair.key_name,
        subnet_id=network["public_subnets"][0].id,
        vpc_security_group_ids=[web_sg.id],
        iam_instance_profile=instance_profile.name,
        user_data=user_data,
        opts=pulumi.ResourceOptions(
            depends_on=list(db_secrets.values()), # NOTE Pulumi will correctly wait for all the SSM parameters to be created before launching the EC2 instance and running user_data.
            delete_before_replace=True  # Ensures Pulumi destroys and recreates the instance
        ),
        tags={
            "Name": "chatbot-server",
            "UserDataHash": user_data_hash  # This tag forces instance replacement when user_data changes
            },
    )


    # Export the instance's public IP and DNS
    pulumi.export("instance_id", instance.id)
    pulumi.export("public_ip", instance.public_ip)
    pulumi.export("public_dns", instance.public_dns)
    pulumi.export("application_url", pulumi.Output.concat("http://", instance.public_dns))
    pulumi.export("db_endpoint", database["instance"].endpoint)
    pulumi.export("db_username", database["username"])
    pulumi.export("db_password", database["password"])
    pulumi.export("db_name", database["database"])

else:

    # Create a launch template for auto scaling
    # This defines how EC2 instances should be launched
    launch_template = aws.ec2.LaunchTemplate(
        "chatbot-launch-template",
        image_id=aws.ec2.get_ami(
            most_recent=True,
            owners=["amazon"],
            filters=[
                aws.ec2.GetAmiFilterArgs(
                    name="name",
                    values=["amzn2-ami-hvm-*-x86_64-gp2"],
                ),
            ],
        ).id,
        instance_type=instance_type,
        key_name=key_pair.key_name,
        vpc_security_group_ids=[web_sg.id],
        user_data=user_data.apply(
            lambda data: base64.b64encode(data.encode("utf-8")).decode("utf-8")
        ),
        iam_instance_profile=aws.ec2.LaunchTemplateIamInstanceProfileArgs(
            name=instance_profile.name,
        ),
        tag_specifications=[
            aws.ec2.LaunchTemplateTagSpecificationArgs(
                resource_type="instance",
                tags={
                    "Name": "chatbot-server",
                    "Environment": "production",
                },
            ),
        ],
    )


    # Create a load balancer security group
    # Allows public HTTP (80) and HTTPS (443) traffic to reach the load balancer
    lb_sg = aws.ec2.SecurityGroup(
        "lb-sg",
        vpc_id=network["vpc"].id,
        description="Allow web traffic to load balancer",
        ingress=[
            aws.ec2.SecurityGroupIngressArgs(
                protocol="tcp",
                from_port=80,
                to_port=80,
                cidr_blocks=["0.0.0.0/0"],
            ),
            aws.ec2.SecurityGroupIngressArgs(
                protocol="tcp",
                from_port=443,
                to_port=443,
                cidr_blocks=["0.0.0.0/0"],
            ),
        ],
        egress=[
            aws.ec2.SecurityGroupEgressArgs(
                protocol="-1",
                from_port=0,
                to_port=0,
                cidr_blocks=["0.0.0.0/0"],
            ),
        ],
    )

    # Allow web servers to receive traffic from the load balancer
    # Allow Load Balancer to Talk to EC2s: This rule allows the web server security group (web_sg) to accept traffic from the load balancer on port 80.
    web_sg_rule = aws.ec2.SecurityGroupRule(
        "web-sg-rule-from-lb",
        type="ingress",
        from_port=80,
        to_port=80,
        protocol="tcp",
        security_group_id=web_sg.id,
        source_security_group_id=lb_sg.id,
    )

    # Create an application load balancer (ALB)
    # Creates an Application Load Balancer:
        # Public-facing (not internal)
        # Spread across multiple public subnets
    load_balancer = aws.lb.LoadBalancer(
        "chatbot-lb",
        internal=False,
        load_balancer_type="application",
        security_groups=[lb_sg.id],
        subnets=[subnet.id for subnet in network["public_subnets"]],
        enable_deletion_protection=False,
        tags={"Name": "chatbot-lb"},
    )

    # Create a target group for the ALB
    # Targets are EC2 instances listening on port 80.
    target_group = aws.lb.TargetGroup(
        "chatbot-tg",
        port=80,
        protocol="HTTP",
        vpc_id=network["vpc"].id,
        target_type="instance",
        health_check=aws.lb.TargetGroupHealthCheckArgs(
            enabled=True,
            path="/",
            port="80",
            protocol="HTTP",
            healthy_threshold=3,
            unhealthy_threshold=3,
            timeout=5,
            interval=30,
        ),
    )

    # Create a listener: 1- Listens on port 80 of the ALB. 2- Forwards traffic to the target group.
    listener = aws.lb.Listener(
        "chatbot-listener",
        load_balancer_arn=load_balancer.arn,
        port=80,
        default_actions=[
            aws.lb.ListenerDefaultActionArgs(
                type="forward",
                target_group_arn=target_group.arn,
            ),
        ],
    )

    # Create an auto scaling group
        # Launches 2–4 EC2 instances based on load.
        # Uses the launch_template.
        # Spreads instances across the public subnets.
        # Attaches to the target group, so traffic can be load-balanced.
    auto_scaling_group = aws.autoscaling.Group(
        "chatbot-asg",
        max_size=4,
        min_size=2,
        desired_capacity=2,
        vpc_zone_identifiers=[subnet.id for subnet in network["public_subnets"]],
        target_group_arns=[target_group.arn],
        health_check_type="ELB",
        health_check_grace_period=300,
        launch_template=aws.autoscaling.GroupLaunchTemplateArgs(
            id=launch_template.id,
            version="$Latest",
        ),
        tags=[
            aws.autoscaling.GroupTagArgs(
                key="Name",
                value="chatbot-server",
                propagate_at_launch=True,
            ),
        ],
    )

    # Create scaling policies
    # Define how many instances to add or remove when scaling is triggered:
        # Scale up: Add 1 instance.
        # Scale down: Remove 1 instance.
        # Both have a cooldown of 5 minutes (300 seconds).
    scale_up_policy = aws.autoscaling.Policy(
        "scale-up-policy",
        autoscaling_group_name=auto_scaling_group.name,
        adjustment_type="ChangeInCapacity",
        scaling_adjustment=1,
        cooldown=300,
    )

    scale_down_policy = aws.autoscaling.Policy(
        "scale-down-policy",
        autoscaling_group_name=auto_scaling_group.name,
        adjustment_type="ChangeInCapacity",
        scaling_adjustment=-1,
        cooldown=300,
    )

    # Create CloudWatch alarms for scaling
    # Set up CloudWatch alarms to trigger scaling:
        # High CPU (>70%) for 2 intervals → scale up.
        # Low CPU (<30%) for 2 intervals → scale down.
        # Based on average EC2 CPU usage over 5-minute periods.
    high_cpu_alarm = aws.cloudwatch.MetricAlarm(
        "high-cpu-alarm",
        comparison_operator="GreaterThanThreshold",
        evaluation_periods=2,
        metric_name="CPUUtilization",
        namespace="AWS/EC2",
        period=300,
        statistic="Average",
        threshold=70,
        alarm_description="Scale up when CPU > 70%",
        alarm_actions=[scale_up_policy.arn],
        dimensions={"AutoScalingGroupName": auto_scaling_group.name},
    )

    low_cpu_alarm = aws.cloudwatch.MetricAlarm(
        "low-cpu-alarm",
        comparison_operator="LessThanThreshold",
        evaluation_periods=2,
        metric_name="CPUUtilization",
        namespace="AWS/EC2",
        period=300,
        statistic="Average",
        threshold=30,
        alarm_description="Scale down when CPU < 30%",
        alarm_actions=[scale_down_policy.arn],
        dimensions={"AutoScalingGroupName": auto_scaling_group.name},
    )

    # Update exports
    pulumi.export("load_balancer_dns", load_balancer.dns_name)
    pulumi.export("application_url", pulumi.Output.concat("http://", load_balancer.dns_name))


