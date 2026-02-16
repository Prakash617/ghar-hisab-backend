#!/bin/bash

# Exit on error
set -e

echo "Waiting for PostgreSQL to be ready..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 1
done

echo "PostgreSQL is up - executing command"

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser if it doesn't exist (optional)
# echo "Creating superuser if needed..."
# python manage.py shell << EOF
# from accounts.models import User
# if not User.objects.filter(email='admin@example.com').exists():
#     User.objects.create_superuser(email='admin@example.com', password='admin123')
# EOF

echo "Starting application..."
exec "$@"
