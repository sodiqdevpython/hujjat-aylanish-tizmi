# Python bazaviy image
FROM python:3.11-slim

# Ishchi papka yaratish
WORKDIR /app

# Kerakli paketlarni o‘rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Loyihani konteynerga nusxalash
COPY . .

# Django serverni ishga tushirish
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
