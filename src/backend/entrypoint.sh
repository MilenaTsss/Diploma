#!/bin/sh

echo "Checking for unapplied model changes..."
python manage.py makemigrations --check --dry-run
if [ $? -ne 0 ]; then
  echo "ERROR: There are model changes that are not reflected in migrations!"
  exit 1
fi

echo "No missing migrations found."

echo "Applying migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating superuser if not exists..."
python manage.py shell << EOF
from users.models import User
phone = '${DJANGO_SUPERUSER_PHONE}'
full_name = '${DJANGO_SUPERUSER_NAME}'
password = '${DJANGO_SUPERUSER_PASSWORD}'

if not User.objects.filter(role=User.Role.SUPERUSER).exists():
    User.objects.create_superuser(
        phone=phone,
        password=password,
        full_name=full_name
    )
EOF


echo "Starting Gunicorn..."
gunicorn --bind 0.0.0.0:8000 backend.wsgi:application \
  --access-logfile - \
  --error-logfile - \
  --access-logformat '{"time": "%(t)s", "status": %(s)s, "method": "%(m)s", "url": "%(U)s", "size": %(b)s, "ip": "%(h)s", "user_agent": "%(a)s"}'
