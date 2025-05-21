**Create a Project Directory**

```
mkdir fastapi-chatbot-aws
cd fastapi-chatbot-aws
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**Create Basic Project Structure**

```
mkdir -p app/api app/core app/models app/services tests infrastructure
touch README.md requirements.txt
```

**Initialize a Pulumi Project**

cd infrastructure
pulumi new aws-python -y

**Deploying the FastAPI App to EC2**

In order to check if the app and nginx running on ec2, you need ssh it and then ue follwing commands:

```
systemctl status chatbot 
systemctl status nginx
```

**Test the Deployed Application**

```
# Using the application_url from Pulumi output
curl http://your-application-url/

# Test the chat endpoint
curl -X POST http://your-application-url/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello, chatbot!"}'

# Test the history endpoint
curl http://your-application-url/history
```

**Verify Database Connectivity**

```
# Connect to one of your EC2 instances
ssh -i your-key.pem ec2-user@your-instance-ip

psql --version

# Connect to the PostgreSQL database
psql -h your-db-endpoint -p 5432 -U dbadmin -d chatbot

# Enter the password when prompted (from Pulumi output). Note that password is saved in /etc/environment (Look at user_data.sh)

# Query the messages table
SELECT * FROM messages;
```

**Monitor the Application Logs**

The easiest way to view startup logs:

1. Go to the AWS Management Console
2. Navigate to EC2 > Instances
3. Select your instance
4. Click on "Actions" > "Monitor and troubleshoot" > "Get system log"

SSH into your instance and check these specific log files, i exists:

ssh -i your-key.pem ec2-user@your-instance-ip

```
# Check application logs
sudo journalctl -u chatbot.service -n 100 --no-pager

sudo cat /var/log/cloud-init-output.log
sudo cat /var/log/cloud-init.log
sudo cat /var/log/user-data-script.log (created by a line on top of the user_data.sh)
```

```
# Nginx logs
sudo cat /var/log/nginx/error.log
sudo cat /var/log/nginx/access.log

# General system logs
sudo cat /var/log/messages
```
