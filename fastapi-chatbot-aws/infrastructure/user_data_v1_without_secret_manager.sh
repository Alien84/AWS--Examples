#!/bin/bash

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


# Install Python and dependencies
yum install -y python3 python3-pip git # postgresql

# Add PostgreSQL repository that's compatible with Amazon Linux 2
amazon-linux-extras enable postgresql14
yum install -y postgresql postgresql-devel

# Install pip dependencies
pip3 install --upgrade pip
pip3 install fastapi uvicorn gunicorn
# Install psycopg2 for PostgreSQL
pip3 install psycopg2-binary sqlalchemy

# Create directory for the application
mkdir -p /opt/chatbot

# Set environment variables for database connection
cat << EOF > /etc/environment
DB_HOST=DB_HOST_PLACEHOLDER
DB_PORT=DB_PORT_PLACEHOLDER
DB_NAME=DB_NAME_PLACEHOLDER
DB_USER=DB_USER_PLACEHOLDER
DB_PASS=DB_PASS_PLACEHOLDER
EOF

set -a
source /etc/environment
set +a

# Clone the application repository (in a real scenario)
# git clone https://github.com/your-username/fastapi-chatbot.git /opt/chatbot


# Create the FastAPI application with database support
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
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

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

# Create a service file for chatbot
cat <<EOF > /etc/systemd/system/chatbot.service
[Unit]
Description=Chatbot FastAPI application
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/opt/chatbot
ExecStart=/usr/local/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app -b 0.0.0.0:8000
Restart=always
EnvironmentFile=/etc/environment

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