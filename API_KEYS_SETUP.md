# API Keys Setup Guide

This guide will help you obtain all necessary API keys and tokens for the RecruitIQ system.

## Required API Keys

### 1. OpenAI API Key

**Purpose**: Powers the AI candidate evaluation system

**How to obtain**:
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in to your account
3. Navigate to API Keys section
4. Click "Create new secret key"
5. Copy the key (starts with `sk-`)
6. Set environment variable: `OPENAI_API_KEY=sk-your-key-here`

**Pricing**: Pay-per-use. GPT-4 costs approximately $0.03 per 1K input tokens and $0.06 per 1K output tokens.

**Recommendations**:
- Set usage limits in OpenAI dashboard
- Monitor usage regularly
- Consider using GPT-3.5-turbo for development (cheaper)

### 2. GitHub Personal Access Token

**Purpose**: Analyzes candidate GitHub profiles and repositories

**How to obtain**:
1. Go to [GitHub Settings - Developer Settings](https://github.com/settings/tokens)
2. Click "Generate new token" > "Generate new token (classic)"
3. Give it a descriptive name: "RecruitIQ Access"
4. Select scopes:
   - `public_repo` (access public repositories)
   - `read:user` (read user profile data)
5. Click "Generate token"
6. Copy the token (starts with `ghp_`)
7. Set environment variable: `GITHUB_TOKEN=ghp_your-token-here`

**Note**: GitHub has rate limits (5,000 requests per hour for authenticated requests). The system handles this gracefully.

### 3. Telegram Bot Token

**Purpose**: Sends evaluation summaries to hiring team via Telegram

**How to obtain**:
1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow instructions to name your bot
4. Copy the HTTP API token provided
5. Set environment variable: `TELEGRAM_BOT_TOKEN=your-token-here`

**Get Chat ID**:
1. Add your bot to a Telegram group or channel
2. Send a message to the group
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Look for `"chat":{"id":` in the JSON response
5. Set environment variable: `TELEGRAM_CHAT_ID=your-chat-id`

**Alternative for personal chat**:
1. Message your bot on Telegram
2. Visit the getUpdates URL above
3. Find your chat ID in the response

### 4. AWS Credentials

**Purpose**: Stores resume files and assessment documents in S3

**How to obtain**:
1. Log in to [AWS Console](https://console.aws.amazon.com/)
2. Go to IAM (Identity and Access Management)
3. Click "Users" > "Add users"
4. Create user: "recruitiq-app"
5. Select "Programmatic access"
6. Attach policies:
   - `AmazonS3FullAccess` (or create custom policy with specific bucket access)
7. Complete user creation
8. Copy Access Key ID and Secret Access Key
9. Set environment variables:
   ```
   AWS_ACCESS_KEY_ID=your-access-key-id
   AWS_SECRET_ACCESS_KEY=your-secret-access-key
   AWS_STORAGE_BUCKET_NAME=your-bucket-name
   AWS_S3_REGION_NAME=us-east-1
   ```

**Create S3 Bucket**:
1. Go to S3 in AWS Console
2. Click "Create bucket"
3. Name: `recruitiq-media-production` (or your chosen name)
4. Region: Choose your preferred region
5. Block all public access: Enabled
6. Versioning: Enabled (recommended)
7. Create bucket

### 5. Database and Redis (Production)

**PostgreSQL on AWS RDS**:
- Use Terraform to provision (see terraform/ directory)
- Or create manually in AWS RDS Console
- Connection string format: `postgresql://user:password@host:5432/database`

**Redis on AWS ElastiCache**:
- Use Terraform to provision (see terraform/ directory)
- Or create manually in AWS ElastiCache Console
- Connection string format: `redis://password@host:6379/0`

## Environment Variables Summary

Create a `.env` file in your project root with all keys:

```env
# Django
DJANGO_SECRET_KEY=your-secret-key-minimum-50-chars
DEBUG=False
ALLOWED_HOSTS=your-domain.com

# Database
DATABASE_URL=postgresql://user:password@host:5432/recruitiq

# Redis
REDIS_URL=redis://password@host:6379/0

# AWS
USE_S3=True
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=recruitiq-media
AWS_S3_REGION_NAME=us-east-1

# OpenAI
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4-turbo-preview

# GitHub
GITHUB_TOKEN=ghp_your-github-token

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

## Security Best Practices

1. **Never commit API keys to Git**
   - Add `.env` to `.gitignore`
   - Use `.env.example` as template

2. **Use environment-specific keys**
   - Development keys for local testing
   - Production keys for live system

3. **Rotate keys regularly**
   - OpenAI: Rotate every 90 days
   - GitHub: Rotate every 90 days
   - AWS: Use IAM roles when possible

4. **Monitor API usage**
   - Set up billing alerts in OpenAI
   - Monitor AWS CloudWatch for unusual activity
   - Check GitHub token usage

5. **Use secrets management**
   - AWS Secrets Manager for production
   - Or environment variables in deployment platform

## Cost Estimation

**OpenAI API**:
- Average evaluation: 2,000 tokens input + 1,500 tokens output
- Cost per evaluation: ~$0.15 (GPT-4)
- 100 candidates/month: ~$15/month

**AWS**:
- S3 storage: $0.023/GB/month
- RDS (db.t3.micro): ~$15/month
- ElastiCache (cache.t3.micro): ~$13/month
- Data transfer: Variable

**GitHub API**:
- Free (within rate limits)

**Telegram Bot**:
- Free

**Total estimated monthly cost**: $50-100 for moderate usage

## Testing API Keys

Test each service individually:

```bash
# Test OpenAI
python -c "from openai import OpenAI; client = OpenAI(api_key='YOUR_KEY'); print(client.models.list())"

# Test GitHub
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user

# Test Telegram
curl https://api.telegram.org/botYOUR_TOKEN/getMe

# Test AWS S3
aws s3 ls --profile recruitiq
```

## Troubleshooting

**OpenAI "Invalid API Key"**:
- Check key starts with `sk-`
- Verify no extra spaces
- Check OpenAI account has credits

**GitHub "Bad credentials"**:
- Token may have expired
- Check scopes are correct
- Regenerate token if needed

**Telegram "Unauthorized"**:
- Verify bot token is correct
- Check bot hasn't been deleted
- Ensure bot is added to chat/group

**AWS "Access Denied"**:
- Check IAM permissions
- Verify bucket name is correct
- Ensure region matches

## Support Resources

- OpenAI: https://help.openai.com/
- GitHub: https://docs.github.com/en/rest
- Telegram Bots: https://core.telegram.org/bots
- AWS Support: https://aws.amazon.com/support/

