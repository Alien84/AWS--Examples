# Install Pulumi

```
curl -fsSL https://get.pulumi.com | sh  # For macOS/Linux
# For Windows, download from https://www.pulumi.com/docs/get-started/install/
```

Then run `pulumi login` or set a `PULUMI_ACCESS_TOKEN`.

Pulumi stores credentials in:
`~/.pulumi/credentials.json `

```
{
    "current": "https://api.pulumi.com",
    "accessTokens": {
        "https://api.pulumi.com": ""
    },
    "accounts": {
        "https://api.pulumi.com": {
            "accessToken": "",
            "username": "",
            "organizations": [
                "alien110"
            ],
            "lastValidatedAt": "2025-05-23T13:56:38.502275+01:00"
        }
    }
}
```

# Create a project:

```

mkdir my-pulumi-project
cd my-pulumi-project
pulumi new python

Using pip:
source venv/bin/activate

```

**Using poetry**
When you create a Pulumi project with  **Poetry** , it automatically uses a **virtual environment** to isolate your project's dependencies.

The location depends slightly on how your Poetry is configured:

* **Default behavior** (most common): Poetry creates the virtual environment **outside** your project folder, typically somewhere like:

`~/.cache/pypoetry/virtualenvs/`

* It creates a separate folder for each project, named something like:

`<your-project-name>-<randomhash>/bin/python`

* **Project-local behavior** (optional): If you configure Poetry to create virtual environments **inside** your project directory, it would appear under:

`./venv/`

You can check **where exactly** the virtualenv is for your project by running this command inside your project:

`poetry env info --path`

It'll print the **full path** to your environment.

---

### How Should You Install New Packages?

When using Poetry, you should **always** install packages using `poetry add` rather than `pip install`.

This way, Poetry updates both your `pyproject.toml` and your `poetry.lock` files properly.

Example to install a new package (e.g., `requests`):

`poetry add requests`

This does 3 things:

* Installs the package into your virtualenv
* Updates your `pyproject.toml` dependencies section
* Locks the exact version into `poetry.lock` for reproducible installs later.

 **Important** :

Don't manually activate the virtualenv and use `pip install`. Poetry manages everything for you safely.

# Create a new stack:

```
pulumi stack init dev

```

Pulumi **creates a new stack** in its backend (local or Pulumi Cloud), **but it does not immediately create a `Pulumi.dev.yaml` file**  **until you set at least one config value or run a deployment** .

```
pulumi config set aws:region eu-west-2

```

# Delete a stack

**Method 1: Force Pulumi Destroy with Refresh**

```
cd infrastructure

# Select your stack
pulumi stack select dev  # or staging/prod

# Refresh the state to sync with actual AWS resources
pulumi refresh --yes

# Now try to destroy
pulumi destroy --yes
```

**Method 2: Check and Fix Pulumi State**

```
cd infrastructure

# Export current state to see what Pulumi thinks exists
pulumi stack export > state-backup.json

# List the stack resources
pulumi stack --show-urns

# If there are orphaned resources, you can remove them from state
# pulumi state delete <resource-urn>  # Use carefully!

# After cleaning state, try destroy again
pulumi destroy --yes
```

**Method 3: Target Specific Resource Groups**

```
cd infrastructure

# Destroy EC2 instances first
pulumi destroy --target "aws:ec2/instance:Instance::*" --yes

# Then destroy auto scaling groups
pulumi destroy --target "aws:autoscaling/group:Group::*" --yes

# Then destroy load balancers
pulumi destroy --target "aws:lb/loadBalancer:LoadBalancer::*" --yes

# Then destroy networking
pulumi destroy --target "aws:ec2/vpc:Vpc::*" --yes

# Finally destroy everything else
pulumi destroy --yes
```

**Method 4: Manual AWS Resource Cleanup**

```
# List EC2 instances for your stack
aws ec2 describe-instances \
  --filters "Name=tag:Environment,Values=dev" "Name=instance-state-name,Values=running,pending,stopping" \
  --query 'Reservations[*].Instances[*].[InstanceId,Tags[?Key==`Name`].Value|[0]]' \
  --output table

# Terminate EC2 instances
aws ec2 terminate-instances --instance-ids i-1234567890abcdef0

# Delete Auto Scaling Groups
aws autoscaling describe-auto-scaling-groups \
  --query 'AutoScalingGroups[?contains(Tags[?Key==`Environment`].Value, `dev`)].AutoScalingGroupName' \
  --output text

aws autoscaling delete-auto-scaling-group --auto-scaling-group-name YOUR_ASG_NAME --force-delete

# Delete Load Balancers
aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[?contains(Tags[?Key==`Environment`].Value, `dev`)].LoadBalancerArn' \
  --output text

aws elbv2 delete-load-balancer --load-balancer-arn YOUR_LB_ARN

# Delete ECR repository (be careful with this!)
aws ecr delete-repository --repository-name chatbot-app --force

# Delete VPC (this will fail if resources are still attached)
aws ec2 describe-vpcs \
  --filters "Name=tag:Name,Values=*chatbot*" \
  --query 'Vpcs[*].[VpcId,Tags[?Key==`Name`].Value|[0]]' \
  --output table
```


**Method 5: Reset Pulumi Stack**

```
cd infrastructure

# Export the stack for backup
pulumi stack export > backup-before-reset.json

# Remove all resources from the Pulumi state (doesn't delete AWS resources)
pulumi stack export | jq '.deployment.resources = []' | pulumi stack import

# Or completely reinitialize the stack
pulumi stack rm dev --yes  # This removes the stack entirely
pulumi stack init dev
pulumi config set aws:region eu-west-2
# Set other configs...
```


**Method 6: Use AWS CLI to Find and Delete Resources by Tags**

```
# Find all resources with your Environment tag
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Environment,Values=dev \
  --query 'ResourceTagMappingList[*].[ResourceARN]' \
  --output text

# Find all resources with your project name
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Project,Values=chatbot \
  --query 'ResourceTagMappingList[*].[ResourceARN]' \
  --output text
```
