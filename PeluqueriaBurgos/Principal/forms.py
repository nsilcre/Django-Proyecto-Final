from django import forms
from django.utils.dateparse import parse_date

from .models import Cita, Peluqueros, Servicio, get_horas_disponibles


class CitaForm(forms.ModelForm):
    class Meta:
        model = Cita
        # El cliente se asigna desde la vista según el usuario autenticado
        # Primero servicio, luego peluquero
        fields = [
            "servicio",
            "peluquero",
            "fecha",
            "hora",
            "motivo",
        ]
        widgets = {
            "servicio": forms.Select(attrs={"class": "form-select"}),
            "peluquero": forms.Select(attrs={"class": "form-select"}),
            "fecha": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "motivo": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Forzamos el flujo de reserva: servicio -> peluquero -> hora
        self.fields["servicio"].required = True
        self.fields["peluquero"].required = True
        self.fields["hora"].required = True

        # Hora como desplegable (se rellena dinámicamente por JS y/o en servidor)
        self.fields["hora"].widget = forms.Select(attrs={"class": "form-select"})
        self.fields["hora"].input_formats = ["%H:%M"]
        self.fields["hora"].choices = [("", "Selecciona una hora")]

        def _get_int(key):
            try:
                return int(self.data.get(key))
            except (TypeError, ValueError):
                return None

        servicio_id = _get_int("servicio") if self.data else None
        peluquero_id = _get_int("peluquero") if self.data else None
        fecha = parse_date(self.data.get("fecha")) if self.data else None

        if not servicio_id and self.instance.pk and self.instance.servicio_id:
            servicio_id = self.instance.servicio_id
        if not peluquero_id and self.instance.pk and self.instance.peluquero_id:
            peluquero_id = self.instance.peluquero_id
        if not fecha and self.instance.pk and self.instance.fecha:
            fecha = self.instance.fecha

        # Por defecto no mostramos peluqueros hasta que se seleccione un servicio
        self.fields["peluquero"].queryset = Peluqueros.objects.none()

        if servicio_id:
            self.fields["peluquero"].queryset = Peluqueros.objects.filter(
                servicios__id=servicio_id
            ).distinct()

        # Si ya tenemos servicio + peluquero + fecha, precargamos horas disponibles (fallback sin JS)
        if servicio_id and peluquero_id and fecha:
            servicio = Servicio.objects.filter(pk=servicio_id).first()
            peluquero = Peluqueros.objects.filter(pk=peluquero_id).first()
            if servicio and peluquero:
                horas = get_horas_disponibles(
                    peluquero=peluquero,
                    fecha=fecha,
                    servicio=servicio,
                    exclude_cita_pk=self.instance.pk if self.instance.pk else None,
                )
                self.fields["hora"].choices = [("", "Selecciona una hora")] + [
                    (h.strftime("%H:%M"), h.strftime("%H:%M")) for h in horas
                ]
