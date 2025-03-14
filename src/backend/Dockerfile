# --- Stage 1: Base Python Image ---
FROM python:3.13 AS base

# Prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /backend_app

# Upgrade pip
RUN pip install --upgrade pip

# Copy the requirements
COPY requirements.txt  .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Development ---
FROM base AS development

# Copy the Django project to the container
COPY . .

# Expose the Django port
EXPOSE 8000

# Run Django’s server after applying migrations
CMD ["sh", "-c", "echo 'Applying migrations...'; python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]

# --- Stage 3: Production (Gunicorn + Nginx)  ---
FROM base AS production

# Copy the Django project to the container
COPY . .

# Expose the Django port
EXPOSE 8000

# Migrate database, Collect static files for admin panel and rest framework, Run Django’s server using gunicorn and configure logging
CMD ["sh", "-c", "echo 'Applying migrations...'; python manage.py migrate && python manage.py collectstatic --noinput && gunicorn --bind 0.0.0.0:8000 backend.wsgi:application --access-logfile - --error-logfile - --access-logformat '{\"time\": \"%(t)s\", \"status\": %(s)s, \"method\": \"%(m)s\", \"url\": \"%(U)s\", \"size\": %(b)s, \"ip\": \"%(h)s\", \"user_agent\": \"%(a)s\"}'"]
