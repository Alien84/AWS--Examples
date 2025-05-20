import pulumi
import pulumi_aws as aws

def create_vpc(name, cidr_block="10.0.0.0/16", include_nat_instance=True):
    # Create a VPC
    vpc = aws.ec2.Vpc(
        f"{name}-vpc",
        cidr_block=cidr_block,
        enable_dns_hostnames=True,
        enable_dns_support=True,
        tags={"Name": f"{name}-vpc"},
    )

    # Create an internet gateway
    igw = aws.ec2.InternetGateway(
        f"{name}-igw",
        vpc_id=vpc.id,
        tags={"Name": f"{name}-igw"},
    )

    # Create public subnets across two availability zones
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

    # Create private subnets across two availability zones
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

    # Create NAT instance if requested
    if include_nat_instance:
        # Create a security group for the NAT instance
        nat_sg = aws.ec2.SecurityGroup(
            f"{name}-nat-sg",
            vpc_id=vpc.id,
            description="Security group for NAT instance",
            ingress=[
                aws.ec2.SecurityGroupIngressArgs(
                    protocol="-1",  # All protocols
                    from_port=0,
                    to_port=0,
                    cidr_blocks=[cidr_block],  # Allow traffic from VPC CIDR
                ),
            ],
            egress=[
                aws.ec2.SecurityGroupEgressArgs(
                    protocol="-1",  # All protocols
                    from_port=0,
                    to_port=0,
                    cidr_blocks=["0.0.0.0/0"],
                ),
            ],
            tags={"Name": f"{name}-nat-sg"},
        )

        # Get an Amazon Linux 2 AMI
        ami = aws.ec2.get_ami(
            most_recent=True,
            owners=["amazon"],
            filters=[
                aws.ec2.GetAmiFilterArgs(
                    name="name",
                    values=["amzn2-ami-hvm-*-x86_64-gp2"],
                ),
            ],
        )

        # Create a NAT instance
        nat_instance = aws.ec2.Instance(
            f"{name}-nat-instance",
            instance_type="t2.micro",  # Free tier eligible
            ami=ami.id,
            subnet_id=public_subnet_a.id,
            associate_public_ip_address=True,
            source_dest_check=False,  # Required for NAT functionality
            vpc_security_group_ids=[nat_sg.id],
            user_data="""#!/bin/bash
            # Enable IP forwarding
            echo 1 > /proc/sys/net/ipv4/ip_forward
            # Make it permanent
            echo "net.ipv4.ip_forward = 1" >> /etc/sysctl.conf
            sysctl -p
            # Configure NAT (MASQUERADE)
            yum install -y iptables-services
            iptables -t nat -A POSTROUTING -o eth0 -s 0.0.0.0/0 -j MASQUERADE
            service iptables save
            systemctl enable iptables
            systemctl start iptables
            """,
            tags={"Name": f"{name}-nat-instance"},
        )

        # Create a route table for private subnets
        private_rt = aws.ec2.RouteTable(
            f"{name}-private-rt",
            vpc_id=vpc.id,
            routes=[
                aws.ec2.RouteTableRouteArgs(
                    cidr_block="0.0.0.0/0",
                    instance_id=nat_instance.id,
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

        return {
            "vpc": vpc,
            "public_subnets": [public_subnet_a, public_subnet_b],
            "private_subnets": [private_subnet_a, private_subnet_b],
            "nat_instance": nat_instance,
        }
    else:
        # Without NAT, private subnets won't have internet access
        return {
            "vpc": vpc,
            "public_subnets": [public_subnet_a, public_subnet_b],
            "private_subnets": [private_subnet_a, private_subnet_b],
        }