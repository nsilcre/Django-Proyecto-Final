from __future__ import annotations

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class UppercaseValidator:
    """Validates that the password contains at least one uppercase letter."""

    def validate(self, password: str, user=None):
        if not any(ch.isupper() for ch in password):
            raise ValidationError(
                _("La contraseña debe contener al menos una letra mayúscula."),
                code="password_no_uppercase",
            )

    def get_help_text(self):
        return _("Tu contraseña debe contener al menos una letra mayúscula.")
