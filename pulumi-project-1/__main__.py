"""A Python Pulumi program"""

import pulumi
import pulumi_aws as aws

## Pulumi coniguration
# Set my public IP address before running pulumi up
# pulumi config set --path "trustedCidrs[0]" "$(curl -s https://ipinfo.io/ip)/32"
# pulumi config set --path "trustedCidrs[1]" "203.0.113.99/32"

config = pulumi.Config()
trusted_cidrs = config.get_object("trustedCidrs") or []
# trusted_cidrs = ["86.191.39.248/32"]  # IP range that’s allowed — ["0.0.0.0/0"] for EVERYONE
app_ports = [22, 80, 443, 8000]       # SSH, HTTP, HTTPS, App Port
env = "dev"
project = "project1"

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
pulumi.export("ami_id", amazon_ami.id)









# NOTE: cidr_blocks
""""
When you want conect ths instance via SSH and if you are going to assign your own IP address to the instance, you should use your public IP addrees.
By assigning your IP addrees, you cannot connect via EC2 Instance Connect. you need to allow only the public IP ranges used by AWS EC2 Instance Connect service.
See https://ip-ranges.amazonaws.com/ip-ranges.json
Those can vary per region and may change over time. So, one solution is use 0.0.0.0/0 to allow all IPs.

To allow only your actual IP, you should find your current public IP by visiting a site like:

📌 https://whatismyipaddress.com/
📌 https://ipinfo.io/

By assigning your IP addrees, you cannot connect via EC2 Instance Connect. 
"""

# Create dynamic ingress rules
ingress_rules = [
    aws.ec2.SecurityGroupIngressArgs(
        protocol="tcp",
        from_port=port,
        to_port=port,
        cidr_blocks=trusted_cidrs,
        description=f"Allow TCP on port {port} from trusted sources"
    )
    for port in app_ports
]

# Create the security group
web_secgroup = aws.ec2.SecurityGroup(f"{project}-{env}-web-sg",
    description="Security group for web servers allowing HTTP, HTTPS, SSH, and app ports",
    ingress=ingress_rules,
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
            description="Allow all outbound traffic"
        )
    ],
    tags={
        "Name": f"{project}-{env}-web-sg",
        "Environment": env,
        "Project": project,
        "Owner": "Ali Akbari"
    }
)

user_data_script = '''#!/bin/bash
# Update and install necessary packages
yum update -y
yum install python3 git -y

# Install FastAPI and Uvicorn
pip3 install fastapi uvicorn

# Create app file
cat <<EOF > /home/ec2-user/app.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/chat")
async def chat(q: str):
    return {"response": f"You said: {q}"}
EOF

# Create a systemd service for FastAPI
cat <<EOF > /etc/systemd/system/fastapi.service
[Unit]
Description=FastAPI server
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user
ExecStart=/usr/local/bin/uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start and enable FastAPI service
systemctl daemon-reload
systemctl enable fastapi
systemctl start fastapi

# Harden SSH - Disable password login: Edit SSH config file:
sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd
'''

### Create a Non-Root User
"""
# Right now, you log in as ec2-user (default AWS user). It’s okay, but even better is to create a new user:
sudo adduser myuser
sudo usermod -aG wheel myuser  # Give sudo (admin) privileges

sudo mkdir /home/myuser/.ssh
sudo cp /home/ec2-user/.ssh/authorized_keys /home/myuser/.ssh/
sudo chown -R myuser:myuser /home/myuser/.ssh

"""

### Turn on Basic EC2 Firewall (iptables or nftables)
"""
# Your AWS Security Group is good, but inside the EC2 machine itself, you can run an additional firewall too.

sudo yum install iptables-services -y

# Allow SSH and your app
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT

# Allow internal traffic (for updates, etc.)
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Drop all other incoming traffic
sudo iptables -P INPUT DROP

# Save rules
sudo service iptables save
sudo systemctl enable iptables
sudo systemctl start iptables
"""

### NOTE """If you ever change your user_data, you must recreate the EC2 instance — because AWS only runs user_data at first boot! pulumi destroy then pulumi up"""

# Launch EC2 instance
server = aws.ec2.Instance(f"{project}-{env}-fastapi-server",
    instance_type="t2.micro",
    security_groups=[web_secgroup.name],
    ami=amazon_ami.id,
    associate_public_ip_address=True,
    user_data=user_data_script,
    key_name='my-keypair'
)

pulumi.export('public_ip', server.public_ip)
