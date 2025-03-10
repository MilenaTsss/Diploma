# Use the official Python runtime image
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

# --- Development Stage ---
FROM base AS development

# Copy the Django project to the container
COPY . .

# Expose the Django port
EXPOSE 8000

# Run Django’s server after applying migrations
CMD ["sh", "-c", "echo 'Applying migrations...'; python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]

# --- Production Stage ---
FROM base AS production

# Copy the Django project to the container
COPY . .

# Expose the Django port
EXPOSE 8000

# Run Django’s server using gunicorn
CMD ["sh", "-c", "echo 'Applying migrations...'; python manage.py migrate && gunicorn --bind 0.0.0.0:8000 backend.wsgi:application"]