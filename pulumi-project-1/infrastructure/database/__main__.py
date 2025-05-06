import pulumi
import pulumi_aws as aws
import pulumi_random as random
from pulumi import Config, Output

"""
# You need set up the configuration to reference the networking stack
# pulumi config set networkStackName <your-org>/<networking-project>/<stack-name>
# run "pulumi stack ls" in networking folder to get "<your-org>/<networking-project>/<stack-name>" 
"""

# Get networking stack reference
config = Config()
network_stack = config.require("networkStackName")
network = pulumi.StackReference(network_stack)

# Get networking resources from the exported values
vpc_id = network.get_output("vpc_id")
private_subnet_ids = network.get_output("private_subnet_ids")
db_sg_id = network.get_output("db_sg_id")

# Generate a random password for the database
db_password = random.RandomPassword("db-password",
    length=16,
    special=True,
    override_special="!#$%&*()-_=+[]{}<>:?"
)

"""
When you create an RDS instance, AWS does not randomly pick subnets. Instead → AWS requires you to provide a Subnet Group, which defines allowed subnets.
    ✅ AWS will then launch the database in one (or more) of those subnets.
    ✅ For high availability (multi-AZ), AWS requires at least 2 subnets in different AZs → so that if one AZ goes down, DB still works.
    ✅ By using private subnets, you make sure:
        🚫 Database is not publicly accessible.
        ✅ Only your app servers inside VPC can reach the DB.
"""

# Create a subnet group for the RDS instance
db_subnet_group = aws.rds.SubnetGroup("db-subnet-group",
    subnet_ids=private_subnet_ids,
    tags={
        "Name": "chatbot-db-subnet-group",
        "Project": "fastapi-chatbot"
    }
)

"""
DS Parameter Group is like a configuration profile for your database engine (PostgreSQL, MySQL, etc). 
It defines the database engine settings → how the database behaves internally.
When you launch an RDS instance, you can attach a Parameter Group.
    If you don't → AWS uses the default one → which might not have the settings you want.
    If you want to customize DB behavior → you need to create and attach your own Parameter Group.

"family="postgres13" → defines the database engine version family.
    postgres13 → means → this parameter group is for PostgreSQL version 13.x
    You must match this with the version of the RDS instance you will create later.

log_connections = 1 → log every time a client connects to the database.
"""

# Create a parameter group for PostgreSQL
db_parameter_group = aws.rds.ParameterGroup("db-param-group",
    family="postgres17",  # Choose the appropriate version
    description="Parameter group for chatbot PostgreSQL",
    parameters=[
        aws.rds.ParameterGroupParameterArgs(
            name="log_connections",
            value="1"
        ),
        aws.rds.ParameterGroupParameterArgs(
            name="log_disconnections",
            value="1"
        )
    ],
    tags={
        "Name": "chatbot-db-param-group",
        "Project": "fastapi-chatbot"
    }
)

# Create the PostgreSQL RDS instance
db_instance = aws.rds.Instance("chatbot-db",
    allocated_storage=20,
    storage_type="gp2",
    engine="postgres",
    engine_version="17.3",  # Choose the appropriate version
    instance_class="db.t3.micro",  # For production, use a larger instance
    db_name="chatbot",
    username="dbadmin",
    password=db_password.result,
    parameter_group_name=db_parameter_group.name,
    db_subnet_group_name=db_subnet_group.name,
    vpc_security_group_ids=[db_sg_id],
    skip_final_snapshot=True,  # For demo purposes only, use false in production
    multi_az=False,  # For production, set to true for high availability
    storage_encrypted=True,  # Encrypt database storage
    tags={
        "Name": "chatbot-db",
        "Project": "fastapi-chatbot"
    }
)

# Export database connection information
pulumi.export("db_endpoint", db_instance.endpoint)
pulumi.export("db_name", db_instance.db_name)
pulumi.export("db_username", db_instance.username)
pulumi.export("db_password", db_password.result)  # In production, use AWS Secrets Manager