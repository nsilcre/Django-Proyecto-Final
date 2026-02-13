import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PeluqueriaBurgos.settings')
django.setup()

from django.contrib.auth.models import User
from django.core.management.base import CommandError

def create_target_user():
    username = "GertrudisMena"
    password = "GertruMena"
    first_name = "Gertrudis"
    last_name = "Mena"
    
    try:
        if User.objects.filter(username=username).exists():
            print(f"El usuario '{username}' ya existe. Actualizando contraseña...")
            user = User.objects.get(username=username)
            user.set_password(password)
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            print(f"Usuario '{username}' actualizado correctamente.")
        else:
            User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            print(f"Usuario '{username}' creado correctamente.")
            
    except Exception as e:
        print(f"Error creando usuario: {e}")

if __name__ == "__main__":
    create_target_user()
