#!/bin/bash
set -e

echo "Waiting for postgres..."
while ! nc -z $DB_HOST 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Creating superuser if needed..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='admin@recruitiq.com').exists():
    User.objects.create_superuser('admin@recruitiq.com', 'changeme')
    print("Superuser created")
END

exec "$@"

