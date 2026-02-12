from __future__ import annotations

import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from Principal.models import Cliente


class Command(BaseCommand):
    help = "Crea (o actualiza) un usuario normal para iniciar sesión en la web."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--email", default="")
        parser.add_argument(
            "--password",
            default=None,
            help="Si no se indica, se pedirá por consola (recomendado).",
        )

    def handle(self, *args, **options):
        User = get_user_model()

        username: str = options["username"]
        email: str = options["email"]
        password: str | None = options["password"]

        if not password:
            while True:
                pw1 = getpass.getpass("Contraseña: ")
                pw2 = getpass.getpass("Repite la contraseña: ")
                if pw1 != pw2:
                    self.stderr.write(self.style.ERROR("Las contraseñas no coinciden."))
                    continue
                password = pw1
                break

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": False,
                "is_superuser": False,
            },
        )

        # Si existía, actualizamos email y aseguramos que no sea staff/superuser
        if not created:
            user.email = email or user.email
            user.is_staff = False
            user.is_superuser = False

        # Validar contraseña según AUTH_PASSWORD_VALIDATORS
        try:
            validate_password(password, user=user)
        except ValidationError as e:
            for msg in e.messages:
                self.stderr.write(self.style.ERROR(str(msg)))
            return

        user.set_password(password)
        user.save()

        # Crear Cliente asociado (opcional, pero deja todo listo)
        Cliente.objects.get_or_create(
            user=user,
            defaults={
                "nombre": user.first_name or user.username,
                "apellido": user.last_name or "",
                "email": user.email or "",
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Usuario creado: {username}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Usuario actualizado: {username}"))
