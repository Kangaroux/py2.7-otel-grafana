#!/bin/sh
set -e

echo "Generating migrations..."
python manage.py makemigrations api --noinput

echo "Running migrations..."
python manage.py migrate --noinput

echo "Seeding sample data..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()
from api.models import Product
if not Product.objects.exists():
    Product.objects.create(name='Widget', price='9.99', description='A useful widget')
    Product.objects.create(name='Gadget', price='24.99', description='An amazing gadget')
    Product.objects.create(name='Doohickey', price='4.99', description='A tiny doohickey')
    print('Created sample products')
else:
    print('Products already exist, skipping seed')
"

echo "Starting Django server on port 8000..."
exec python manage.py runserver 0.0.0.0:8000
