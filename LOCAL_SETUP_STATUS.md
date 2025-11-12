# RecruitIQ Local Setup Status

## ✅ Completed

1. **Replaced pnpm with Bun** - Updated all package management to use Bun
2. **Dockerized the entire application** - All services running in Docker:
   - PostgreSQL database
   - Redis for Celery
   - Django backend
   - Celery worker
   - React frontend with Bun
3. **Fixed migrations** - Django migrations are now auto-generated on container startup
4. **Created API client** - Frontend API client structure in place

## 🔄 Current Status

### Backend (Port 8000)
- ✅ Container running
- ✅ Database connected
- ✅ Migrations created and applied automatically
- ✅ Superuser creation script in place (admin@recruitiq.com / admin123)
- ⚠️ Getting 500 errors due to SECRET_KEY configuration issue

### Frontend (Port 8080)
- ✅ Container running
- ✅ Webpack compiling
- ⚠️ Tailwind CSS configuration needs adjustment for custom CSS variables

### Services
```
recruitiq-backend-1    Running on 0.0.0.0:8000
recruitiq-db-1         Running on 0.0.0.0:5432 (healthy)
recruitiq-redis-1      Running on 0.0.0.0:6379 (healthy)
recruitiq-celery-1     Running
recruitiq-frontend-1   Running on 0.0.0.0:8080
```

## 🔧 Quick Fixes Needed

### 1. Backend SECRET_KEY Issue
The SECRET_KEY environment variable needs to be properly set. Currently defined in docker-compose.yml but not being read.

**Quick Fix**: Check `backend/project_name/settings/local.py` SECRET_KEY configuration

### 2. Frontend Tailwind CSS
Custom CSS variables (like `bg-background`) aren't being recognized by Tailwind.

**Quick Fix**: Simplify the CSS or update tailwind.config.ts to recognize custom properties

## 🚀 How to Use

### Start Everything
```bash
docker-compose up -d
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Stop Everything
```bash
docker-compose down
```

### Fresh Start (with database reset)
```bash
docker-compose down -v
docker-compose up -d
```

### Access Services
- Frontend: http://localhost:8080
- Backend API: http://localhost:8000/api/
- Django Admin: http://localhost:8000/admin/
- API Schema: http://localhost:8000/api/schema/

### Default Credentials
- Email: admin@recruitiq.com
- Password: admin123

## 📝 Next Steps

1. Fix SECRET_KEY configuration in backend
2. Simplify Tailwind CSS or configure it properly
3. Test the complete flow:
   - Login
   - Create job description
   - Upload resume
   - View candidate evaluations

## 🐛 Known Issues

1. Backend returns 500 errors due to SECRET_KEY
2. Frontend has Tailwind compilation errors
3. Some API endpoints may need testing once the above are fixed

## 📦 Environment Variables

The following environment variables are configured in `docker-compose.yml`:
- `DJANGO_SETTINGS_MODULE=project_name.settings.local`
- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `DEBUG=True`
- `OPENAI_API_KEY` (optional)
- `GITHUB_TOKEN` (optional)
- `TELEGRAM_BOT_TOKEN` (optional)

