# RecruitIQ - AI-Powered Recruitment System

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE.txt)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-19.2-blue.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-blue.svg)](https://www.typescriptlang.org/)

An intelligent recruitment platform that leverages AI to evaluate candidate resumes, analyze GitHub profiles, and provide comprehensive assessments to hiring teams.

## 🎯 Features

### Core Capabilities
- **Bulk Resume Processing**: Upload up to 10 resumes simultaneously
- **AI-Powered Evaluation**: OpenAI GPT-4 analyzes candidates against job descriptions
- **GitHub Integration**: Automatically detects and analyzes candidate GitHub profiles
- **Intelligent Scoring**: Provides 1-10 overall scores with detailed breakdowns
- **Interview Recommendations**: Clear "Interview" or "Decline" decisions with reasoning
- **Stakeholder Notifications**: Real-time Telegram notifications to hiring teams
- **Audit Trail**: Complete processing logs for transparency and debugging
- **PDF Reports**: Generates professional 2-page assessment documents

### Technical Highlights
- **Concurrent Processing**: Handles 10+ candidates simultaneously without data contamination
- **Robust Error Handling**: Gracefully handles API failures, rate limits, and invalid data
- **Async Architecture**: Celery-based task queue for efficient background processing
- **Production-Ready**: Includes tests, CI/CD, monitoring, and deployment configurations
- **Type-Safe**: TypeScript frontend and Python type hints with pyrefly
- **Modern UI**: Beautiful Shadcn UI components with dark mode support

## 🏗️ Technology Stack

### Frontend
- **React 19.2** with TypeScript
- **Shadcn UI** (Radix UI + TailwindCSS)
- **React Router** for navigation
- **Biome** for linting and formatting
- **Jest** for testing
- **Webpack** for bundling

### Backend
- **Django 5.0** with Python 3.12
- **Django REST Framework** for APIs
- **Celery** for async task processing
- **PostgreSQL** for data storage
- **Redis** for caching and message broker
- **django-allauth** for authentication

### AI & Integrations
- **OpenAI GPT-4** for candidate evaluation
- **PyGithub** for GitHub API integration
- **python-telegram-bot** for notifications
- **ReportLab** for PDF generation
- **PyPDF2** for resume parsing

### Infrastructure (AWS)
- **ECS Fargate** for containerized deployments
- **RDS PostgreSQL** with multi-AZ
- **ElastiCache Redis** for high availability
- **S3** for file storage
- **Application Load Balancer** for traffic distribution
- **CloudWatch** for logging and monitoring
- **Terraform** for infrastructure as code

## 📋 Prerequisites

- Python 3.12+
- Node.js 22+
- Poetry (Python dependency management)
- Bun (JavaScript runtime and package manager)
- PostgreSQL 15+
- Redis 7+
- Docker and Docker Compose (for containerized deployment)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/recruitiq.git
cd recruitiq
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

Required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key
- `GITHUB_TOKEN`: GitHub personal access token
- `TELEGRAM_BOT_TOKEN`: Telegram bot token
- `TELEGRAM_CHAT_ID`: Telegram chat/group ID
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME` (for S3)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string

### 3. Install Backend Dependencies

```bash
cd backend
poetry install
```

### 4. Install Frontend Dependencies

```bash
cd ../  # Back to project root
bun install
```

### 5. Run Database Migrations

```bash
cd backend
poetry run python manage.py migrate
poetry run python manage.py createsuperuser
```

### 6. Create a Job Description

```bash
poetry run python manage.py shell
```

```python
from recruitment.models import JobDescription

JobDescription.objects.create(
    title="Senior Python Developer",
    description="Looking for an experienced Python developer with Django expertise",
    required_skills=["Python", "Django", "REST APIs", "PostgreSQL"],
    nice_to_have_skills=["React", "AWS", "Docker"],
    experience_years=5,
    is_active=True
)
```

### 7. Start Development Servers

**Terminal 1 - Django Backend**:
```bash
cd backend
poetry run python manage.py runserver
```

**Terminal 2 - Celery Worker**:
```bash
cd backend
poetry run celery -A project_name worker --loglevel=info
```

**Terminal 3 - Frontend**:
```bash
bun dev
```

Access the application at http://localhost:8000

## 📚 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design and data flow diagrams
- **[PROJECT_DETAILS.md](PROJECT_DETAILS.md)** - Original project requirements

## 🧪 Running Tests

### Backend Tests

```bash
cd backend
poetry run pytest --cov --reuse-db
```

### Frontend Tests

```bash
bun test
```

### Linting

```bash
# Backend (Python)
cd backend
poetry run ruff check .
poetry run ruff format .
poetry run pyrefly .

# Frontend (TypeScript/JavaScript)
bun lint
bun lint:fix
```

## 🐳 Docker Deployment

### Development

```bash
docker-compose up -d
```

### Production

```bash
docker-compose -f docker-compose.prod.yml up -d
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive production deployment instructions.

## 📊 How It Works

### Candidate Processing Pipeline

1. **Upload**: User uploads resume(s) via the web interface
2. **Parse**: System extracts text from PDF/DOC/TXT files
3. **Analyze Resume**: AI evaluates skills, experience, and qualifications
4. **GitHub Detection**: Automatically finds GitHub profile in resume
5. **GitHub Analysis**: Fetches and analyzes repositories, languages, and contributions
6. **AI Evaluation**: GPT-4 generates comprehensive assessment with scores
7. **Generate Report**: Creates professional 2-page PDF document
8. **Notify**: Sends summary to hiring team via Telegram with action buttons

### Concurrency & Safety

- Each candidate is processed independently in a separate Celery task
- Database transactions with row-level locking prevent data contamination
- Complete audit trail via ProcessingLog model
- Automatic retries for transient failures
- Graceful degradation when external APIs fail

## 🔒 Security

- Email-based authentication with django-allauth
- Session-based authentication for web app
- CSRF protection on all state-changing operations
- API keys stored as environment variables
- S3 buckets with private ACLs
- Input validation and sanitization
- Rate limiting on API endpoints
- Secure password hashing (PBKDF2)

## 📈 Performance

- API response time: < 200ms (p95)
- Resume processing: 2-5 minutes end-to-end
- Concurrent processing: 10+ candidates simultaneously
- Dashboard load time: < 1 second
- Support for 100+ concurrent users

## 📜 License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.
