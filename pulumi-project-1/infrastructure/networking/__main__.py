"""An AWS Python Pulumi program"""

import pulumi
import pulumi_aws as aws

"""
10.0.0.0/16 means:
    -- The VPC can contain up to 65,536 IP addresses (from 10.0.0.0 to 10.0.255.255).
    -- This is a large private IP range, suitable for subdividing into subnets later.

** enable_dns_hostnames=True
    -- This tells AWS to enable DNS hostnames for instances launched in this VPC.
    -- If this is True, instances will get public DNS hostnames if they have public IPs (or private DNS names if private).

** enable_dns_support=True,
    -- This allows instances in the VPC to resolve AWS-provided DNS names.
    -- This is required if you want instances to resolve domain names, e.g., to reach AWS services or external services via DNS.

When you create servers or services inside a VPC, they often need to:
    Call external services (like APIs → api.openai.com)
    Resolve other AWS resources (like my-database.cluster-xyz.us-east-1.rds.amazonaws.com)
    Use internal service discovery (like private DNS names between your microservices)

If DNS is disabled, your servers inside the VPC won’t be able to use domain names — only IP addresses.
This makes everything harder or even impossible.
"""

# Create a VPC
vpc = aws.ec2.Vpc("chatbot-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={
        "Name": "chatbot-vpc",
        "Project": "fastapi-chatbot"
    }
)

"""
An Internet Gateway (IGW) is like the bridge between your private AWS VPC and the public internet.
Without an Internet Gateway, anything inside your VPC (EC2 instances, containers, etc.):
    🚫 Cannot access the internet (no downloads, no updates, no calling external APIs)
    🚫 Cannot be accessed from the internet (no incoming HTTP traffic, no ssh)
"""

# Create an Internet Gateway
igw = aws.ec2.InternetGateway("chatbot-igw",
    vpc_id=vpc.id,
    tags={
        "Name": "chatbot-igw",
        "Project": "fastapi-chatbot"
    }
)

"""
By itself, this does NOT make anything public yet — for that, you need to:
    1. Create subnets
    2. Update route tables to point 0.0.0.0/0 (everything) → to this IGW

10.0.1.0/24 means:
    The subnet has 256 IP addresses (10.0.1.0 to 10.0.1.255).
    AWS reserves 5, so you can actually use 251 IP addresses

map_public_ip_on_launch=True
This is very important → this makes this subnet a public subnet.
When an EC2 instance (or other resource) is launched in this subnet:
    -- It will automatically get a public IP address assigned, unless overridden.
    -- That public IP will allow incoming and outgoing internet traffic (if security groups and route table allow).
If this was False → instances would only get private IPs → no internet access without extra work (like NAT Gateway)

availability_zone="ew-west-2a
    this means this subnet will be in AZ "a" of region "ew-west-2" 
"""

# Create 2 public subnets in different AZs for high availability
public_subnet_a = aws.ec2.Subnet("public-subnet-a",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="eu-west-2a",  # Change to your region's AZ
    map_public_ip_on_launch=True,
    tags={
        "Name": "chatbot-public-subnet-a",
        "Project": "fastapi-chatbot"
    }
)

public_subnet_b = aws.ec2.Subnet("public-subnet-b",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone="eu-west-2b",  # Change to your region's AZ
    map_public_ip_on_launch=True,
    tags={
        "Name": "chatbot-public-subnet-b",
        "Project": "fastapi-chatbot"
    }
)

# Create 2 private subnets for database and future use
private_subnet_a = aws.ec2.Subnet("private-subnet-a",
    vpc_id=vpc.id,
    cidr_block="10.0.3.0/24",
    availability_zone="eu-west-2a",  # Change to your region's AZ
    tags={
        "Name": "chatbot-private-subnet-a",
        "Project": "fastapi-chatbot"
    }
)

private_subnet_b = aws.ec2.Subnet("private-subnet-b",
    vpc_id=vpc.id,
    cidr_block="10.0.4.0/24",
    availability_zone="eu-west-2b",  # Change to your region's AZ
    tags={
        "Name": "chatbot-private-subnet-b",
        "Project": "fastapi-chatbot"
    }
)


"""
A route table is like a set of rules for traffic routing → it tells AWS where traffic should go when leaving a subnet.
    cidr_block="0.0.0.0/0" → means "all traffic to any IP address in the world".
    gateway_id=igw.id → means "send that traffic to the Internet Gateway".
Without this route: 🚫 Even with map_public_ip_on_launch=True, your instances would NOT be able to talk to the internet.
"""

# Create a route table for public subnets
public_route_table = aws.ec2.RouteTable("public-rt",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        ),
    ],
    tags={
        "Name": "chatbot-public-rt",
        "Project": "fastapi-chatbot"
    }
)

# Associate route table with public subnets
public_rt_assoc_a = aws.ec2.RouteTableAssociation("public-rt-assoc-a",
    subnet_id=public_subnet_a.id,
    route_table_id=public_route_table.id
)

public_rt_assoc_b = aws.ec2.RouteTableAssociation("public-rt-assoc-b",
    subnet_id=public_subnet_b.id,
    route_table_id=public_route_table.id
)


"""
NAT stands for Network Address Translation.
    A NAT Gateway allows private instances (in private subnets) to:

    ✅ Initiate outbound connections to the internet (e.g., download packages, call APIs, update OS).
    🚫 BUT it blocks inbound connections from the internet → meaning internet cannot initiate connections to the private instances.

This creates an Elastic IP (EIP).
    -- Elastic IP is a static, public IP address that stays assigned to your AWS account until released.
    -- vpc=True → means this EIP is for use inside your VPC (which is required for NAT Gateway).

vpc=True → means this EIP is for use inside your VPC (which is required for NAT Gateway).

subnet_id=public_subnet_a.id → places this NAT Gateway inside the public subnet you created earlier.
    ✅ Why inside public subnet?
        -- The NAT Gateway needs internet access → public subnets have internet via IGW.
        -- Private subnets will route traffic → to NAT Gateway → which will go through public subnet → then out to internet.
"""

# creates an Elastic IP (EIP) and Create a NAT Gateway for private subnets
eip = aws.ec2.Eip("nat-eip",
    domain="vpc",
    tags={
        "Name": "chatbot-nat-eip",
        "Project": "fastapi-chatbot"
    }
)

nat_gateway = aws.ec2.NatGateway("chatbot-nat-gw",
    allocation_id=eip.id,
    subnet_id=public_subnet_a.id,
    tags={
        "Name": "chatbot-nat-gw",
        "Project": "fastapi-chatbot"
    }
)

# Create a route table for private subnets
private_route_table = aws.ec2.RouteTable("private-rt",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            nat_gateway_id=nat_gateway.id,
        ),
    ],
    tags={
        "Name": "chatbot-private-rt",
        "Project": "fastapi-chatbot"
    }
)

# Associate route table with private subnets
private_rt_assoc_a = aws.ec2.RouteTableAssociation("private-rt-assoc-a",
    subnet_id=private_subnet_a.id,
    route_table_id=private_route_table.id
)

private_rt_assoc_b = aws.ec2.RouteTableAssociation("private-rt-assoc-b",
    subnet_id=private_subnet_b.id,
    route_table_id=private_route_table.id
)



# Create security group for web servers, such as static websites or 
# This open the instance to the world
web_sg = aws.ec2.SecurityGroup("web-sg",
    description="Allow web traffic",
    vpc_id=vpc.id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"],
            description="Allow HTTP from anywhere"
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=443,
            to_port=443,
            cidr_blocks=["0.0.0.0/0"],
            description="Allow HTTPS from anywhere"
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr_blocks=["0.0.0.0/0"],  # In production, restrict to your IP
            description="Allow SSH from anywhere (restrict in production)"
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",  # All protocols
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
            description="Allow all outbound traffic"
        ),
    ],
    tags={
        "Name": "chatbot-web-sg",
        "Project": "fastapi-chatbot"
    }
)

# Create security group for the database
db_sg = aws.ec2.SecurityGroup("db-sg",
    description="Allow database traffic",
    vpc_id=vpc.id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=5432,  # PostgreSQL
            to_port=5432,
            security_groups=[web_sg.id],
            description="Allow PostgreSQL from web servers"
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",  # All protocols
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
            description="Allow all outbound traffic"
        ),
    ],
    tags={
        "Name": "chatbot-db-sg",
        "Project": "fastapi-chatbot"
    }
)

# Create security group for load balancer
lb_sg = aws.ec2.SecurityGroup("lb-sg",
    description="Allow traffic to load balancer",
    vpc_id=vpc.id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"],
            description="Allow HTTP from anywhere"
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=443,
            to_port=443,
            cidr_blocks=["0.0.0.0/0"],
            description="Allow HTTPS from anywhere"
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",  # All protocols
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
            description="Allow all outbound traffic"
        ),
    ],
    tags={
        "Name": "chatbot-lb-sg",
        "Project": "fastapi-chatbot"
    }
)

# Update the security group for web servers to only accept traffic from the load balancer
# This is for aplication servers (FastAPI)
#   -- SHOULD NOT be open to the world directly
#   -- SHOULD NOT receive HTTP/HTTPS directly from the internet SHOULD ONLY accept traffic from your Load Balancer (lb-sg) on FastAPI port (8000)
app_sg = aws.ec2.SecurityGroup("app-sg",
    description="Allow application traffic",
    vpc_id=vpc.id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=8000,  # FastAPI port
            to_port=8000,
            security_groups=[lb_sg.id],
            description="Allow traffic from load balancer to FastAPI"
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr_blocks=["0.0.0.0/0"],  # In production, restrict to your IP
            description="Allow SSH from anywhere (restrict in production)"
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",  # All protocols
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
            description="Allow all outbound traffic"
        ),
    ],
    tags={
        "Name": "chatbot-app-sg",
        "Project": "fastapi-chatbot"
    }
)

# Export values that will be needed by other stacks
pulumi.export("vpc_id", vpc.id)
pulumi.export("public_subnet_ids", [public_subnet_a.id, public_subnet_b.id])
pulumi.export("private_subnet_ids", [private_subnet_a.id, private_subnet_b.id])
pulumi.export("web_sg_id", web_sg.id)
pulumi.export("db_sg_id", db_sg.id)
pulumi.export("lb_sg_id", lb_sg.id)
pulumi.export("app_sg_id", app_sg.id)


