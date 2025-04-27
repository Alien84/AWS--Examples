import pulumi
from pulumi_aws import rds

# Define a new RDS instance
db_instance = rds.Instance('my-db-instance',
    allocated_storage=20,
    engine='postgres',
    engine_version='17.2',
    instance_class='db.t3.micro',
    db_name='mydatabase',
    username='admanijehmin',
    password='alien110Secure',  # It's recommended to use Pulumi config for passwords
    publicly_accessible=True,
    skip_final_snapshot=True)

# Export the instance endpoint
pulumi.export('db_endpoint', db_instance.endpoint)

"""
Step 4: Connect to Your Database
With the database endpoint, you can connect to your PostgreSQL instance using any standard SQL client:
- Ensure your network settings (like security groups) allow connections from your client’s IP address.

Step 5: Implementing Best Practices and Security
- Security: Ensure that your RDS instance is not publicly accessible if it contains sensitive data. Adjust the `publicly_accessible` parameter as needed.
- Backups: Enable automated backups and define the backup retention period to ensure data durability.
- Multi-AZ Deployments: For production workloads, consider enabling Multi-AZ deployments for high availability.
"""