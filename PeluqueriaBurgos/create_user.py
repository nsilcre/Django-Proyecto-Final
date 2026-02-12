import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PeluqueriaBurgos.settings')
django.setup()

from django.contrib.auth.models import User

username = "GertrudisMena"
email = "gertrudis@example.com"
password = "GertrudisMena"
first_name = "Gertrudis"
last_name = "Mena Pavón"

if not User.objects.filter(username=username).exists():
    User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name
    )
    print(f"User {username} created successfully.")
else:
    print(f"User {username} already exists.")
