# RecruitIQ Architecture

## System Overview

RecruitIQ is a full-stack AI-powered recruitment system that processes candidate resumes, evaluates them against job descriptions, and provides detailed assessments to hiring teams.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          Frontend (React + TypeScript)           │
│                          - Dashboard                             │
│                          - Upload Interface                      │
│                          - Candidate Details                     │
│                          - Evaluation Viewer                     │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS/REST API
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    Django Backend (Python)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   REST API   │  │    Admin     │  │  Auth        │          │
│  │  (DRF)       │  │   Interface  │  │  (Allauth)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Business Logic                         │  │
│  │  • Models (JobDescription, Candidate, Evaluation)        │  │
│  │  • Serializers & ViewSets                                │  │
│  │  • File Upload Handler                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────┬──────────────────────────┬──────────────────┬─────┘
             │                          │                  │
             │                          │                  │
    ┌────────▼─────────┐      ┌────────▼────────┐   ┌────▼─────┐
    │   PostgreSQL     │      │    Redis        │   │  AWS S3  │
    │   (Database)     │      │   (Cache/Queue) │   │  (Files) │
    └──────────────────┘      └─────────┬───────┘   └──────────┘
                                        │
                                        │ Celery Tasks
                                        │
              ┌─────────────────────────▼─────────────────────────┐
              │             Celery Workers (Async Processing)     │
              │                                                   │
              │  ┌────────────────────────────────────────────┐  │
              │  │  Pipeline Stages:                          │  │
              │  │  1. Extract Resume Text (PyPDF2)           │  │
              │  │  2. Detect GitHub Profile (Regex)          │  │
              │  │  3. Fetch GitHub Data (PyGithub)           │  │
              │  │  4. Evaluate with AI (OpenAI GPT-4)        │  │
              │  │  5. Generate PDF Report (ReportLab)        │  │
              │  │  6. Send Telegram Notification             │  │
              │  └────────────────────────────────────────────┘  │
              └───────────┬───────────┬───────────┬──────────────┘
                          │           │           │
                    ┌─────▼─────┐ ┌──▼──────┐ ┌─▼────────────┐
                    │  OpenAI   │ │ GitHub  │ │   Telegram   │
                    │    API    │ │   API   │ │     Bot      │
                    └───────────┘ └─────────┘ └──────────────┘
```

## Component Details

### Frontend Layer

**Technology Stack**:
- React 19.2 with TypeScript
- React Router for navigation
- Shadcn UI components (built on Radix UI)
- TailwindCSS for styling
- Axios for API calls

**Key Components**:
- `Dashboard`: Overview of all candidates with statistics
- `UploadResumes`: Drag-and-drop file upload interface (max 10 files)
- `CandidateDetail`: Detailed view of candidate with evaluation
- `EvaluationCard`: Rich display of AI assessment results
- `FileUpload`: Reusable upload component with validation
- `CandidateTable`: Sortable/filterable table with status badges

**Build Process**:
- Webpack bundles frontend assets
- TypeScript compilation with strict mode
- Biome for linting and formatting
- Jest for testing

### Backend Layer

**Technology Stack**:
- Django 5.0 with Python 3.12
- Django REST Framework for APIs
- django-allauth for authentication
- Celery for async task processing
- PostgreSQL for data persistence
- Redis for caching and message broker

**Apps**:
1. **users**: Custom user model with email authentication
2. **recruitment**: Core recruitment logic
3. **common**: Shared utilities and base models

**API Endpoints**:
- `/api/recruitment/job-descriptions/` - CRUD for job postings
- `/api/recruitment/candidates/` - Candidate management
- `/api/recruitment/candidates/upload-resumes/` - Bulk resume upload
- `/api/recruitment/candidates/{id}/reprocess/` - Retry failed processing
- `/api/recruitment/evaluations/` - View assessments
- `/api/recruitment/processing-logs/` - Audit trail
- `/accounts/*` - django-allauth authentication

### Data Models

**JobDescription**:
- Stores job requirements, skills, experience level
- One-to-many with Candidates

**Candidate**:
- Personal information (name, email, phone, LinkedIn)
- Status tracking (pending → processing → completed/failed)
- Celery task ID for async tracking
- Foreign key to JobDescription

**Resume**:
- File storage (local or S3)
- Parsed text content
- File metadata

**GitHubProfile**:
- Cached GitHub data
- Repository analysis
- Language statistics
- Contribution metrics

**Evaluation**:
- Overall score (1-10)
- Detailed analysis (JSON)
- Recommendation (interview/decline)
- Generated PDF report
- Processing time and model used

**ProcessingLog**:
- Complete audit trail
- Stage-by-stage status
- Error messages
- Timestamps

**StakeholderFeedback**:
- Telegram responses
- Approval/rejection/comments
- Stakeholder identity

### Async Processing Pipeline

**Celery Architecture**:
- **Broker**: Redis
- **Result Backend**: Redis
- **Workers**: Multiple concurrent workers
- **Beat**: Scheduled tasks (if needed)

**Processing Stages**:

1. **File Upload** (Synchronous)
   - Validate file types and sizes
   - Create Candidate and Resume records
   - Trigger async processing task

2. **Resume Parsing** (Celery Task)
   - Extract text from PDF/DOC/TXT
   - Handle encoding issues
   - Store parsed text

3. **GitHub Detection** (Celery Task)
   - Regex search for GitHub URLs
   - Extract username
   - Handle various URL formats

4. **GitHub Data Fetch** (Celery Task)
   - API calls to fetch profile
   - Repository enumeration
   - Language analysis
   - Rate limit handling
   - Cache results

5. **AI Evaluation** (Celery Task)
   - Build comprehensive prompt
   - Call OpenAI GPT-4 API
   - Parse structured JSON response
   - Retry on failures
   - Validate output

6. **Document Generation** (Celery Task)
   - Create 2-page PDF assessment
   - Include charts and visualizations
   - Store in S3

7. **Telegram Notification** (Celery Task)
   - Format message with key findings
   - Add action buttons
   - Send to hiring team channel

**Concurrency & Safety**:
- Each candidate processed independently
- Database transactions with row-level locking
- No shared state between tasks
- Idempotent operations (safe to retry)
- Comprehensive error handling

### External Integrations

**OpenAI GPT-4**:
- Model: `gpt-4-turbo-preview`
- Structured output with JSON mode
- Temperature: 0.3 (consistent results)
- Max tokens: 3000
- Retry logic with exponential backoff

**GitHub API**:
- PyGithub library
- Authenticated requests (higher rate limits)
- Graceful degradation if profile unavailable
- Caching to minimize API calls

**Telegram Bot**:
- python-telegram-bot library
- Inline keyboard for feedback
- Webhook handler for responses
- Message threading for organization

**AWS S3**:
- django-storages integration
- Presigned URLs for secure access
- Lifecycle policies for old files
- Versioning enabled

### Security

**Authentication**:
- Email-based with django-allauth
- Session authentication for web
- CSRF protection
- Password hashing with PBKDF2

**Authorization**:
- DRF permission classes
- Users only see their submissions
- Admins have full access
- Row-level permission checks

**Data Protection**:
- All API keys in environment variables
- S3 buckets are private
- Database connections encrypted
- HTTPS in production

**Input Validation**:
- File type restrictions
- Size limits (10MB per file, max 10 files)
- Serializer validation
- SQL injection protection (ORM)

### Deployment Architecture (AWS)

**Infrastructure**:
- VPC with public and private subnets
- Application Load Balancer (public)
- ECS Fargate for Django backend (private)
- RDS PostgreSQL (private, multi-AZ)
- ElastiCache Redis (private)
- S3 for media files
- CloudWatch for logging and monitoring

**High Availability**:
- Multiple availability zones
- Auto-scaling ECS tasks
- RDS automated backups
- Redis replication
- Load balancer health checks

**Monitoring**:
- CloudWatch logs for all services
- Custom metrics for processing pipeline
- Sentry for error tracking
- Cost monitoring and alerts

## Data Flow

### Candidate Submission Flow

```
1. User uploads resume(s) via frontend
   ↓
2. Frontend sends multipart/form-data to API
   ↓
3. Django validates and creates Candidate + Resume records
   ↓
4. Celery task triggered (async)
   ↓
5. Task processes through pipeline stages
   ↓
6. Each stage logs progress to ProcessingLog
   ↓
7. Final evaluation saved to database
   ↓
8. Telegram notification sent
   ↓
9. Frontend polls for updates or receives via WebSocket
```

### Evaluation Retrieval Flow

```
1. User views candidate detail page
   ↓
2. Frontend fetches candidate data
   ↓
3. API returns candidate with nested evaluation
   ↓
4. Frontend displays EvaluationCard component
   ↓
5. User can download PDF assessment
   ↓
6. S3 presigned URL generated for secure download
```

## Scalability Considerations

**Horizontal Scaling**:
- Stateless Django backend (can run multiple instances)
- Celery workers can be scaled independently
- RDS read replicas for read-heavy workloads
- Redis Cluster for high throughput

**Vertical Scaling**:
- Increase ECS task memory/CPU
- Larger RDS instance types
- Bigger Redis nodes

**Optimization Strategies**:
- Database indexing on frequently queried fields
- Redis caching for job descriptions
- S3 CDN (CloudFront) for static assets
- Lazy loading in frontend
- Pagination on list views

## Disaster Recovery

**Backup Strategy**:
- RDS automated backups (7 days retention)
- Manual snapshots before major changes
- S3 versioning for all uploaded files
- Database dumps to S3 (weekly)

**Recovery Procedures**:
- Point-in-time RDS restore
- S3 object restoration from versions
- Terraform state for infrastructure recreation
- Code deployment from Git

## Performance Metrics

**Target SLAs**:
- API response time: < 200ms (p95)
- Resume processing: < 5 minutes (end-to-end)
- File upload: < 10 seconds (10MB file)
- Dashboard load: < 1 second
- Concurrent users: 100+
- Processing throughput: 10+ candidates/minute

## Future Enhancements

- Real-time WebSocket updates
- Advanced search and filtering
- Interview scheduling integration
- Email notifications as alternative to Telegram
- Multi-language support
- Custom evaluation criteria per job
- Candidate ranking and comparison
- Integration with ATS systems
- Video interview analysis
- Skills assessment tests

