import pulumi
import pulumi_aws as aws

def create_vpc(name, cidr_block="10.0.0.0/16"):
    # Create a VPC

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
    vpc = aws.ec2.Vpc(
        f"{name}-vpc",
        cidr_block=cidr_block,
        enable_dns_hostnames=True,
        enable_dns_support=True,
        tags={"Name": f"{name}-vpc"},
    )

    # Create an internet gateway
    """
    An Internet Gateway (IGW) is like the bridge between your private AWS VPC and the public internet.
    Without an Internet Gateway, anything inside your VPC (EC2 instances, containers, etc.):
        🚫 Cannot access the internet (no downloads, no updates, no calling external APIs)
        🚫 Cannot be accessed from the internet (no incoming HTTP traffic, no ssh)
    """
    igw = aws.ec2.InternetGateway(
        f"{name}-igw",
        vpc_id=vpc.id,
        tags={"Name": f"{name}-igw"},
    )

    # Create public and private subnets across two availability zones
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
    public_subnet_a = aws.ec2.Subnet(
        f"{name}-public-subnet-a",
        vpc_id=vpc.id,
        cidr_block="10.0.1.0/24",
        availability_zone=f"{aws.config.region}a",
        map_public_ip_on_launch=True,
        tags={"Name": f"{name}-public-subnet-a"},
    )

    public_subnet_b = aws.ec2.Subnet(
        f"{name}-public-subnet-b",
        vpc_id=vpc.id,
        cidr_block="10.0.2.0/24",
        availability_zone=f"{aws.config.region}b",
        map_public_ip_on_launch=True,
        tags={"Name": f"{name}-public-subnet-b"},
    )

    private_subnet_a = aws.ec2.Subnet(
        f"{name}-private-subnet-a",
        vpc_id=vpc.id,
        cidr_block="10.0.3.0/24",
        availability_zone=f"{aws.config.region}a",
        tags={"Name": f"{name}-private-subnet-a"},
    )

    private_subnet_b = aws.ec2.Subnet(
        f"{name}-private-subnet-b",
        vpc_id=vpc.id,
        cidr_block="10.0.4.0/24",
        availability_zone=f"{aws.config.region}b",
        tags={"Name": f"{name}-private-subnet-b"},
    )

    # Create a route table for public subnets
    """
    A route table is like a set of rules for traffic routing → it tells AWS where traffic should go when leaving a subnet.
        cidr_block="0.0.0.0/0" → means "all traffic to any IP address in the world".
        gateway_id=igw.id → means "send that traffic to the Internet Gateway".
    Without this route: 🚫 Even with map_public_ip_on_launch=True, your instances would NOT be able to talk to the internet.
    """
    public_rt = aws.ec2.RouteTable(
        f"{name}-public-rt",
        vpc_id=vpc.id,
        routes=[
            aws.ec2.RouteTableRouteArgs(
                cidr_block="0.0.0.0/0",
                gateway_id=igw.id,
            ),
        ],
        tags={"Name": f"{name}-public-rt"},
    )

    # Associate public subnets with the public route table
    public_rta_a = aws.ec2.RouteTableAssociation(
        f"{name}-public-rta-a",
        subnet_id=public_subnet_a.id,
        route_table_id=public_rt.id,
    )

    public_rta_b = aws.ec2.RouteTableAssociation(
        f"{name}-public-rta-b",
        subnet_id=public_subnet_b.id,
        route_table_id=public_rt.id,
    )

    # Create a NAT gateway for private subnets
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
    eip = aws.ec2.Eip(f"{name}-nat-eip")

    nat_gateway = aws.ec2.NatGateway(
        f"{name}-nat-gateway",
        allocation_id=eip.id,
        subnet_id=public_subnet_a.id,
        tags={"Name": f"{name}-nat-gateway"},
    )

    # Create a route table for private subnets
    private_rt = aws.ec2.RouteTable(
        f"{name}-private-rt",
        vpc_id=vpc.id,
        routes=[
            aws.ec2.RouteTableRouteArgs(
                cidr_block="0.0.0.0/0",
                nat_gateway_id=nat_gateway.id,
            ),
        ],
        tags={"Name": f"{name}-private-rt"},
    )

    # Associate private subnets with the private route table
    private_rta_a = aws.ec2.RouteTableAssociation(
        f"{name}-private-rta-a",
        subnet_id=private_subnet_a.id,
        route_table_id=private_rt.id,
    )

    private_rta_b = aws.ec2.RouteTableAssociation(
        f"{name}-private-rta-b",
        subnet_id=private_subnet_b.id,
        route_table_id=private_rt.id,
    )

    # Return relevant resources
    return {
        "vpc": vpc,
        "public_subnets": [public_subnet_a, public_subnet_b],
        "private_subnets": [private_subnet_a, private_subnet_b],
        "nat_gateway": nat_gateway,
    }