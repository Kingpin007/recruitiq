FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.7.1

# Set working directory
WORKDIR /app

# Copy dependency files from project root
COPY pyproject.toml ./
COPY poetry.lock* ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry lock --no-update 2>/dev/null || true \
    && poetry install --no-interaction --no-ansi

# Copy backend application code
COPY backend/ .

# Create directories
RUN mkdir -p media staticfiles

# Create entrypoint script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Waiting for postgres..."\n\
while ! nc -z db 5432; do\n\
  sleep 0.1\n\
done\n\
echo "PostgreSQL started"\n\
\n\
if [ -z "$DJANGO_SETTINGS_MODULE" ]; then\n\
  export DJANGO_SETTINGS_MODULE=project_name.settings.local\n\
fi\n\
\n\
echo "Creating migrations..."\n\
python manage.py makemigrations --noinput\n\
\n\
echo "Running migrations..."\n\
python manage.py migrate --noinput\n\
\n\
echo "Collecting static files..."\n\
python manage.py collectstatic --noinput || true\n\
\n\
echo "Creating superuser if needed..."\n\
python manage.py shell << END\n\
from django.contrib.auth import get_user_model\n\
User = get_user_model()\n\
if not User.objects.filter(email="admin@recruitiq.com").exists():\n\
    User.objects.create_superuser(email="admin@recruitiq.com", password="admin123")\n\
    print("Superuser created: admin@recruitiq.com / admin123")\n\
END\n\
\n\
exec "$@"' > /entrypoint.sh && chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
