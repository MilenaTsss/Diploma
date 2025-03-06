# Use the official Python runtime image
FROM python:3.11

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

# Copy the Django project to the container
COPY . .

# Expose the Django port
EXPOSE 8000

# Run Django’s server
# CMD ["sh", "-c", "if [ \"$DJANGO_ENV\" = 'production' ]; then gunicorn --bind 0.0.0.0:8000 backend.wsgi:application; else python manage.py runserver 0.0.0.0:8000; fi"]
CMD ["sh", "-c", "echo 'Выполняем миграции...'; python manage.py migrate; if [ \"$DJANGO_ENV\" = 'production' ]; then echo 'Запускаем Gunicorn...'; gunicorn --bind 0.0.0.0:8000 backend.wsgi:application; else echo 'Запускаем Django runserver...'; python manage.py runserver 0.0.0.0:8000; fi"]