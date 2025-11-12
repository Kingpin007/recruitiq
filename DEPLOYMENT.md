# Deployment Guide

This guide covers deploying RecruitIQ to AWS using Terraform, Docker, and various deployment strategies.

## Prerequisites

- AWS Account with admin access
- AWS CLI installed and configured
- Terraform >= 1.0 installed
- Docker and Docker Compose installed
- Domain name (optional but recommended)
- All API keys obtained (see API_KEYS_SETUP.md)

## Architecture Overview

```
Internet → Route53 → ALB → ECS (Django) → RDS PostgreSQL
                      ↓
                    ECS (Celery Workers) → ElastiCache Redis
                      ↓
                    S3 (Media Files)
```

## Step 1: Initial Setup

### 1.1 Clone and Configure

```bash
git clone https://github.com/your-org/recruitiq.git
cd recruitiq
```

### 1.2 Create Environment Files

```bash
# Copy example environment file
cp .env.example .env

# Edit with your actual values
nano .env
```

### 1.3 Configure AWS CLI

```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Default region: us-east-1
# Default output format: json
```

## Step 2: Infrastructure Provisioning with Terraform

### 2.1 Initialize Terraform

```bash
cd terraform/

# Initialize Terraform
terraform init

# Create terraform.tfvars file
cat > terraform.tfvars <<EOF
aws_region = "us-east-1"
project_name = "recruitiq"
environment = "production"

# Database
db_username = "recruitiq_admin"
db_password = "your-strong-password-here"  # CHANGE THIS

# Redis
redis_auth_token = "your-redis-auth-token"  # CHANGE THIS

# Allowed origins for S3 CORS
allowed_origins = ["https://your-domain.com"]
EOF
```

### 2.2 Plan and Apply

```bash
# Review planned changes
terraform plan

# Apply changes (will take 15-20 minutes)
terraform apply

# Save outputs
terraform output > ../terraform-outputs.txt
```

### 2.3 Note Important Outputs

After `terraform apply`, note these values:
- `alb_dns_name`: Load balancer DNS
- `rds_endpoint`: Database connection string
- `redis_endpoint`: Redis connection string
- `s3_bucket_name`: S3 bucket for media files

## Step 3: Database Setup

### 3.1 Update DATABASE_URL

```bash
# In your .env file, update:
DATABASE_URL=postgresql://recruitiq_admin:your-password@<rds_endpoint>/recruitiq
REDIS_URL=redis://:your-redis-auth-token@<redis_endpoint>:6379/0
```

### 3.2 Run Migrations

```bash
cd ../backend

# Install dependencies
poetry install

# Run migrations
poetry run python manage.py migrate

# Create superuser
poetry run python manage.py createsuperuser
```

## Step 4: Build and Push Docker Images

### 4.1 Create ECR Repositories

```bash
aws ecr create-repository --repository-name recruitiq-backend
aws ecr create-repository --repository-name recruitiq-celery
```

### 4.2 Build and Push Images

```bash
# Get ECR login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <your-account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build images
docker build -t recruitiq-backend:latest -f backend/Dockerfile.prod backend/
docker build -t recruitiq-celery:latest -f backend/Dockerfile.prod backend/

# Tag images
docker tag recruitiq-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/recruitiq-backend:latest
docker tag recruitiq-celery:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/recruitiq-celery:latest

# Push images
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/recruitiq-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/recruitiq-celery:latest
```

## Step 5: Deploy to ECS

### 5.1 Create Task Definitions

Create `ecs-task-definition.json`:

```json
{
  "family": "recruitiq-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::<account-id>:role/recruitiq-ecs-task-execution-role",
  "taskRoleArn": "arn:aws:iam::<account-id>:role/recruitiq-ecs-task-role",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/recruitiq-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "DEBUG", "value": "False"},
        {"name": "USE_S3", "value": "True"}
      ],
      "secrets": [
        {"name": "DATABASE_URL", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "REDIS_URL", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "OPENAI_API_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/recruitiq",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "backend"
        }
      }
    }
  ]
}
```

### 5.2 Register Task Definition

```bash
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json
```

### 5.3 Create ECS Service

```bash
aws ecs create-service \
  --cluster recruitiq-cluster \
  --service-name recruitiq-backend-service \
  --task-definition recruitiq-backend \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=DISABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=backend,containerPort=8000"
```

## Step 6: Frontend Deployment to Vercel

### 6.1 Install Vercel CLI

```bash
npm install -g vercel
```

### 6.2 Configure vercel.json

```json
{
  "builds": [
    {
      "src": "frontend/js/index.tsx",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "frontend/webpack_bundles"
      }
    }
  ],
  "routes": [
    {
      "src": "/static/(.*)",
      "dest": "/static/$1"
    },
    {
      "src": "/api/(.*)",
      "dest": "https://your-alb-dns-name.amazonaws.com/api/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ],
  "env": {
    "REACT_APP_API_URL": "https://api.your-domain.com"
  }
}
```

### 6.3 Deploy to Vercel

```bash
# Login to Vercel
vercel login

# Deploy
cd frontend/
vercel --prod
```

## Step 7: Domain Configuration

### 7.1 Create Route53 Hosted Zone

```bash
aws route53 create-hosted-zone --name your-domain.com --caller-reference $(date +%s)
```

### 7.2 Point Domain to ALB

```bash
# Get ALB DNS name
aws elbv2 describe-load-balancers --names recruitiq-alb --query 'LoadBalancers[0].DNSName'

# Create A record (ALIAS)
# Use Route53 console or CLI to create ALIAS record pointing to ALB
```

### 7.3 SSL Certificate

```bash
# Request certificate in ACM
aws acm request-certificate \
  --domain-name your-domain.com \
  --validation-method DNS \
  --subject-alternative-names www.your-domain.com

# Add HTTPS listener to ALB
aws elbv2 create-listener \
  --load-balancer-arn <alb-arn> \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=<cert-arn> \
  --default-actions Type=forward,TargetGroupArn=<target-group-arn>
```

## Step 8: Celery Workers Deployment

### 8.1 Create Celery Worker Task Definition

Similar to backend but with command:

```json
{
  "command": ["celery", "-A", "project_name", "worker", "--loglevel=info"]
}
```

### 8.2 Create Celery Worker Service

```bash
aws ecs create-service \
  --cluster recruitiq-cluster \
  --service-name recruitiq-celery-worker \
  --task-definition recruitiq-celery \
  --desired-count 4 \
  --launch-type FARGATE
```

## Step 9: Monitoring and Logging

### 9.1 CloudWatch Dashboards

```bash
# Create dashboard for key metrics
aws cloudwatch put-dashboard --dashboard-name RecruitIQ --dashboard-body file://cloudwatch-dashboard.json
```

### 9.2 Set Up Alarms

```bash
# High CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name recruitiq-high-cpu \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold
```

## Step 10: Testing the Deployment

### 10.1 Health Checks

```bash
# Test backend health
curl https://your-domain.com/api/schema/

# Test ALB health
curl https://<alb-dns-name>/api/schema/
```

### 10.2 Upload Test Resume

1. Access dashboard at `https://your-domain.com`
2. Log in with superuser credentials
3. Upload a test resume
4. Monitor CloudWatch logs for processing
5. Check Telegram for notification

## Troubleshooting

### Logs

```bash
# Backend logs
aws logs tail /ecs/recruitiq --follow

# Celery worker logs
aws logs tail /ecs/recruitiq-celery --follow
```

### Common Issues

**Database Connection Failed**:
- Check security group rules
- Verify RDS endpoint in DATABASE_URL
- Check VPC configuration

**S3 Access Denied**:
- Verify IAM role has S3 permissions
- Check S3 bucket policy
- Verify bucket name in environment variables

**Celery Tasks Not Processing**:
- Check Redis connectivity
- Verify Celery workers are running
- Check CloudWatch logs for errors

## Maintenance

### Update Application

```bash
# Build new image
docker build -t recruitiq-backend:v1.1.0 -f backend/Dockerfile.prod backend/

# Push to ECR
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/recruitiq-backend:v1.1.0

# Update ECS service
aws ecs update-service \
  --cluster recruitiq-cluster \
  --service recruitiq-backend-service \
  --force-new-deployment
```

### Database Backups

```bash
# Manual snapshot
aws rds create-db-snapshot \
  --db-instance-identifier recruitiq-postgres \
  --db-snapshot-identifier recruitiq-snapshot-$(date +%Y%m%d)

# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier recruitiq-postgres-restored \
  --db-snapshot-identifier recruitiq-snapshot-20240101
```

### Cost Optimization

1. Use Reserved Instances for predictable workloads
2. Enable S3 lifecycle policies
3. Right-size RDS and Redis instances
4. Use Spot Instances for Celery workers (non-critical)
5. Set up Cost Explorer and budgets

## Security Checklist

- [ ] All secrets in AWS Secrets Manager
- [ ] S3 buckets have block public access enabled
- [ ] RDS and Redis in private subnets
- [ ] Security groups follow principle of least privilege
- [ ] SSL/TLS certificates configured
- [ ] Database encrypted at rest
- [ ] Regular security updates applied
- [ ] IAM roles instead of access keys where possible
- [ ] CloudTrail enabled for audit logging
- [ ] MFA enabled for AWS root account

## Scaling Guide

### Auto-Scaling ECS Services

```bash
# Configure auto-scaling
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/recruitiq-cluster/recruitiq-backend-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# CPU-based scaling policy
aws application-autoscaling put-scaling-policy \
  --policy-name cpu-scaling \
  --service-namespace ecs \
  --resource-id service/recruitiq-cluster/recruitiq-backend-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

## Support and Resources

- AWS Documentation: https://docs.aws.amazon.com/
- Django Deployment: https://docs.djangoproject.com/en/stable/howto/deployment/
- Terraform AWS Provider: https://registry.terraform.io/providers/hashicorp/aws/latest/docs

