#!/bin/bash

echo "🚀 Starting RecruitIQ Local Development Environment"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Stop any running containers
echo "🛑 Stopping any existing containers..."
docker-compose down

# Build and start containers
echo "🔨 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if backend is ready
echo "🔍 Checking backend health..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/schema/ > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start. Check logs with: docker-compose logs backend"
        exit 1
    fi
    sleep 2
done

# Check if frontend is ready
echo "🔍 Checking frontend health..."
for i in {1..30}; do
    if curl -s http://localhost:8080 > /dev/null 2>&1; then
        echo "✅ Frontend is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Frontend failed to start. Check logs with: docker-compose logs frontend"
        exit 1
    fi
    sleep 2
done

echo ""
echo "✅ RecruitIQ is running!"
echo ""
echo "📊 Access the application:"
echo "   Frontend: http://localhost:8000"
echo "   Django Admin: http://localhost:8000/admin"
echo ""
echo "🔑 Default superuser credentials:"
echo "   Email: admin@recruitiq.com"
echo "   Password: admin123"
echo ""
echo "📝 Useful commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart: docker-compose restart"
echo "   Backend shell: docker-compose exec backend python manage.py shell"
echo ""
echo "🎯 Next steps:"
echo "   1. Go to http://localhost:8000"
echo "   2. Login with the credentials above"
echo "   3. Create a job description in Django admin"
echo "   4. Upload resumes to test the system"
echo ""

