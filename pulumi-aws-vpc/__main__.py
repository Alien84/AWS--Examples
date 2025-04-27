import pulumi
from pulumi_aws import ec2

# Create a VPC
vpc = ec2.Vpc('my-vpc',
    cidr_block='10.0.0.0/16',
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={
        'Name': 'MyVPC'
    })

# Create subnets
subnet1 = ec2.Subnet('my-subnet-1',
    vpc_id=vpc.id,
    cidr_block='10.0.1.0/24',
    availability_zone='eu-west-2a',
    tags={
        'Name': 'MySubnet1'
    })

subnet2 = ec2.Subnet('my-subnet-2',
    vpc_id=vpc.id,
    cidr_block='10.0.2.0/24',
    availability_zone='eu-west-2b',
    tags={
        'Name': 'MySubnet2'
    })

# Create an Internet Gateway
igw = ec2.InternetGateway('my-igw',
    vpc_id=vpc.id,
    tags={
        'Name': 'MyInternetGateway'
    })

# Create a Route Table and a route
route_table = ec2.RouteTable('my-route-table',
    vpc_id=vpc.id,
    routes=[{
        'cidr_block': '0.0.0.0/0',
        'gateway_id': igw.id
    }],
    tags={
        'Name': 'MyRouteTable'
    })

# Associate Route Table with the subnets
ec2.RouteTableAssociation('my-rta1',
    subnet_id=subnet1.id,
    route_table_id=route_table.id)

ec2.RouteTableAssociation('my-rta2',
    subnet_id=subnet2.id,
    route_table_id=route_table.id)