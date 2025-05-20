#!/bin/bash

# Configure AWS CLI to use IMDSv2
mkdir -p ~/.aws
cat << EOF > ~/.aws/config
[default]
imds_version = v2
EOF

# Extensive logging
exec > >(tee /var/log/user-data-script.log 2>&1)

# Exit immediately if a command exits with a non-zero status
set -e

# Run as root (not needed if this script is run by EC2 as user_data)
#yum update -y is enough, no need for sudo in user_data
yum update -y

# Enable and install NGINX from amazon-linux-extras
amazon-linux-extras enable nginx1
yum clean metadata
yum install -y nginx

# Install AWS CLI and other dependencies
yum install -y python3 python3-pip git awscli amazon-cloudwatch-agent # postgresql

# Add PostgreSQL repository that's compatible with Amazon Linux 2
amazon-linux-extras enable postgresql14
yum install -y postgresql postgresql-devel

# Install application dependencies
pip3 install --upgrade pip
pip3 install fastapi uvicorn gunicorn psycopg2-binary sqlalchemy boto3
# Install psycopg2 for PostgreSQL
pip3 install psycopg2-binary sqlalchemy

# Create application directory
mkdir -p /opt/chatbot
mkdir -p /opt/chatbot/logs

# Create a script to fetch database credentials
cat <<EOF > /opt/chatbot/get_secrets.py
import boto3
import os
import sys

def get_parameters(path_prefix):
    try:
        # Debug messages to stderr
        print(f"Attempting to fetch parameters from path: {path_prefix}", file=sys.stderr)
        
        # Create an SSM client
        session = boto3.session.Session(region_name='eu-west-2')  # Use your region
        ssm = session.client(service_name='ssm')
        
        # Get all parameters under the specified path
        print(f"Fetching parameters by path: {path_prefix}", file=sys.stderr)
        # response = ssm.get_parameters_by_path(
        #     Path=path_prefix,
        #     WithDecryption=True,
        #     Recursive=True
        # )
        
        # parameters = {}
        # for param in response.get('Parameters', []):
        #     param_name = param['Name'].split('/')[-1]
        #     parameters[param_name] = param['Value']

        paginator = ssm.get_paginator('get_parameters_by_path')
        parameters = {}

        for page in paginator.paginate(Path=path_prefix, WithDecryption=True, Recursive=True):
            for param in page['Parameters']:
                param_name = param['Name'].split('/')[-1]
                parameters[param_name] = param['Value']

        print(f"Fetched parameters: {parameters}", file=sys.stderr)   
        return parameters
    
    except Exception as e:
        print(f"Error fetching parameters: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return {}

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python get_secrets.py <parameter_path>", file=sys.stderr)
        sys.exit(1)
    
    path_prefix = sys.argv[1]
    print(f"Starting script with path: {path_prefix}", file=sys.stderr)
    params = get_parameters(path_prefix)
    
    if not params:
        print("No parameters found or error occurred.", file=sys.stderr)
        # Set fallback values for local testing
        print("DB_USERNAME=dbadmin")
        print("DB_PASSWORD=local_test_only")
        print("DB_HOST=localhost")
        print("DB_PORT=5432")
        print("DB_DBNAME=chatbot")
        sys.exit(1)
    
    # Output environment variables
    for key, value in params.items():
        print(f"DB_{key.upper()}={value}")
EOF

# Set execute permissions
chmod +x /opt/chatbot/get_secrets.py

# Create a script to set up environment variables
cat << EOF > /opt/chatbot/setup_env.sh
#!/bin/bash

# Get database credentials from SSM Parameter Store
python3 /opt/chatbot/get_secrets.py ${DB_PARAM_PATH} > /tmp/db_env.sh 2> /opt/chatbot/logs/ssm_fetch.log
sudo mv /tmp/db_env.sh /etc/profile.d/db_env.sh

sudo chmod +x /etc/profile.d/db_env.sh
EOF

chmod +x /opt/chatbot/setup_env.sh

# Execute the setup script
/opt/chatbot/setup_env.sh

# Verify the environment file was created
if [ -f /etc/profile.d/db_env.sh ]; then
    echo "Environment file created successfully" >> /opt/chatbot/logs/ssm_fetch.log
    cat /etc/profile.d/db_env.sh >> /opt/chatbot/logs/ssm_fetch.log
else
    echo "ERROR: Environment file was not created!" >> /opt/chatbot/logs/ssm_fetch.log
fi

# Clone the application repository (in a real scenario)
# git clone https://github.com/your-username/fastapi-chatbot.git /opt/chatbot

# Copy application code
cat <<EOF > /opt/chatbot/main.py
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os

# Get database credentials from environment variables
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_DBNAME = os.getenv("DB_DBNAME")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DATABASE_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DBNAME}"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define database models
class MessageRecord(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    response = Column(Text)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI models
class Message(BaseModel):
    content: str

class ChatResponse(BaseModel):
    response: str

app = FastAPI(title="Chatbot API")

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"status": "online", "message": "Welcome to the Chatbot API"}

@app.post("/chat", response_model=ChatResponse)
def chat(message: Message, db: Session = Depends(get_db)):
    # Simple echo response for now
    response = f"You said: {message.content}"
    
    # Store message in database
    db_message = MessageRecord(content=message.content, response=response)
    db.add(db_message)
    db.commit()
    
    return ChatResponse(response=response)

@app.get("/history")
def get_history(db: Session = Depends(get_db)):
    messages = db.query(MessageRecord).all()
    return {"history": [{"content": msg.content, "response": msg.response} for msg in messages]}
EOF

# Create a service file for systemd
cat <<EOF > /etc/systemd/system/chatbot.service
[Unit]
Description=Chatbot FastAPI application
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/opt/chatbot
EnvironmentFile=/etc/profile.d/db_env.sh
ExecStart=/usr/local/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app -b 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Set permissions
chown -R ec2-user:ec2-user /opt/chatbot

# Start and enable FastAPI service
systemctl daemon-reload
systemctl enable chatbot
systemctl start chatbot


# Configure Nginx
cat <<EOF > /etc/nginx/conf.d/chatbot.conf
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

# Start Nginx
systemctl enable nginx
systemctl start nginx