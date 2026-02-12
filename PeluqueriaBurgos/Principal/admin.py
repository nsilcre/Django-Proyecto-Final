from datetime import date

from django import forms
from django.contrib import admin, messages
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import path

from Principal.models import (
    APERTURA,
    CIERRE,
    COMIDA_FIN,
    COMIDA_INICIO,
    Cita,
    Cliente,
    HorarioPeluquero,
    Peluqueros,
    Servicio,
    TurnoPeluquero,
)


def _turno_intervalo(turno: str):
    if turno == TurnoPeluquero.Turno.MANANA:
        return APERTURA, COMIDA_INICIO
    if turno == TurnoPeluquero.Turno.TARDE:
        return COMIDA_FIN, CIERRE
    # COMPLETO
    return None


class BulkTurnosPorFechasForm(forms.Form):
    """Asignación masiva por fechas.

    Guarda 1 fila por peluquero (no crea slots), así no carga la BD.
    """

    peluqueros = forms.ModelMultipleChoiceField(
        queryset=Peluqueros.objects.all().order_by("nombre", "apellido"),
        widget=FilteredSelectMultiple("Peluqueros", is_stacked=False),
    )

    fecha_inicio = forms.DateField(
        label="Fecha inicio",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    fecha_fin = forms.DateField(
        label="Fecha fin",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    turno = forms.ChoiceField(
        label="Turno",
        choices=TurnoPeluquero.Turno.choices,
        widget=forms.RadioSelect,
        initial=TurnoPeluquero.Turno.MANANA,
    )

    activo = forms.BooleanField(initial=True, required=False)

    reemplazar = forms.BooleanField(
        label="Reemplazar turnos que se solapen",
        required=False,
        help_text="Si marcas esto, se borrarán los turnos existentes que se solapen con este rango para esos peluqueros.",
    )

    def clean(self):
        cleaned = super().clean()
        fi: date | None = cleaned.get("fecha_inicio")
        ff: date | None = cleaned.get("fecha_fin")
        if fi and ff and ff < fi:
            raise forms.ValidationError("La fecha fin no puede ser anterior a la fecha inicio.")
        return cleaned


@admin.register(Peluqueros)
class PeluquerosAdmin(admin.ModelAdmin):
    list_display = ("nombre", "apellido")
    search_fields = ("nombre", "apellido")
    change_list_template = "admin/principal/peluqueros/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "bulk-horarios/",
                self.admin_site.admin_view(self.bulk_horarios_view),
                name="principal_peluqueros_bulk_horarios",
            )
        ]
        return custom + urls

    def bulk_horarios_view(self, request):
        # Mantengo la URL /bulk-horarios/ por compatibilidad, pero ahora es por fechas.
        if request.method == "POST":
            form = BulkTurnosPorFechasForm(request.POST)
            if form.is_valid():
                peluqueros = list(form.cleaned_data["peluqueros"])
                fi = form.cleaned_data["fecha_inicio"]
                ff = form.cleaned_data["fecha_fin"]
                turno = form.cleaned_data["turno"]
                activo = bool(form.cleaned_data.get("activo"))
                reemplazar = bool(form.cleaned_data.get("reemplazar"))

                qs = TurnoPeluquero.objects.filter(peluquero__in=peluqueros)

                # Solape: inicio <= ff y fin >= fi
                solape_q = Q(fecha_inicio__lte=ff, fecha_fin__gte=fi)

                if reemplazar:
                    borrados, _ = qs.filter(solape_q).delete()
                    to_create = [
                        TurnoPeluquero(
                            peluquero=p,
                            fecha_inicio=fi,
                            fecha_fin=ff,
                            turno=turno,
                            activo=activo,
                        )
                        for p in peluqueros
                    ]
                    TurnoPeluquero.objects.bulk_create(to_create)
                    messages.success(
                        request,
                        f"Turnos asignados por fechas. Borrados (solape): {borrados}. Creados: {len(to_create)}.",
                    )
                    return redirect("..")

                # Sin reemplazar: actualizar exactos, crear los que no existan exactos.
                exactos_qs = qs.filter(
                    fecha_inicio=fi,
                    fecha_fin=ff,
                    turno=turno,
                )
                updated = exactos_qs.update(activo=activo)

                existentes_ids = set(exactos_qs.values_list("peluquero_id", flat=True))
                to_create = [
                    TurnoPeluquero(
                        peluquero=p,
                        fecha_inicio=fi,
                        fecha_fin=ff,
                        turno=turno,
                        activo=activo,
                    )
                    for p in peluqueros
                    if p.id not in existentes_ids
                ]
                if to_create:
                    TurnoPeluquero.objects.bulk_create(to_create)

                messages.success(
                    request,
                    f"Turnos asignados por fechas. Creados: {len(to_create)}. Actualizados: {updated}.",
                )
                return redirect("..")
        else:
            form = BulkTurnosPorFechasForm()

        context = {
            **self.admin_site.each_context(request),
            "title": "Asignar turnos por fechas",
            "form": form,
            "opts": self.model._meta,
        }
        return render(request, "admin/principal/peluqueros/bulk_horarios.html", context)


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "duracion_minutos", "precio", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre",)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "apellido", "email", "telefono")
    search_fields = ("nombre", "apellido", "email", "telefono")


class HorarioPeluqueroBulkAddForm(forms.ModelForm):
    """Alta rápida semanal.

    Crea 1 horario por día (un tramo por turno) para no cargar la base de datos.
    """

    # Cerrado los domingos -> no lo mostramos en el alta masiva
    _DIAS_SIN_DOMINGO = [
        (v, label)
        for (v, label) in HorarioPeluquero.DiaSemana.choices
        if int(v) != HorarioPeluquero.DiaSemana.DOMINGO
    ]

    dias_semana = forms.MultipleChoiceField(
        label="Días de la semana",
        choices=_DIAS_SIN_DOMINGO,
        widget=forms.CheckboxSelectMultiple,
        help_text="Selecciona uno o varios días para crear el mismo horario.",
    )

    TURNOS = (
        ("MANANA", "Mañana (08:00–13:30)"),
        ("TARDE", "Tarde (15:00–21:00)"),
    )

    turno = forms.ChoiceField(
        label="Turno",
        choices=TURNOS,
        widget=forms.RadioSelect,
        initial="MANANA",
        help_text="Se creará 1 tramo por día según el turno seleccionado.",
    )

    class Meta:
        model = HorarioPeluquero
        # Nota: el modelo tiene dia_semana/hora_inicio/hora_fin, aquí creamos muchos registros automáticamente
        fields = ("peluquero", "dias_semana", "turno", "activo")

    def clean_dias_semana(self):
        dias = self.cleaned_data.get("dias_semana")
        if not dias:
            raise forms.ValidationError("Selecciona al menos un día.")
        return dias


@admin.register(HorarioPeluquero)
class HorarioPeluqueroAdmin(admin.ModelAdmin):
    list_display = ("peluquero", "dia_semana", "hora_inicio", "hora_fin", "activo")
    list_filter = ("peluquero", "dia_semana", "activo")
    ordering = ("peluquero", "dia_semana", "hora_inicio")


@admin.register(TurnoPeluquero)
class TurnoPeluqueroAdmin(admin.ModelAdmin):
    list_display = ("peluquero", "fecha_inicio", "fecha_fin", "turno", "activo")
    list_filter = ("turno", "activo")
    search_fields = ("peluquero__nombre", "peluquero__apellido")
    ordering = ("-fecha_inicio", "peluquero")

    def get_form(self, request, obj=None, **kwargs):
        # En 'add' usamos el formulario con multiselección.
        if obj is None:
            kwargs["form"] = HorarioPeluqueroBulkAddForm
        return super().get_form(request, obj, **kwargs)

    def save_model(self, request, obj, form, change):
        # En edición usamos el flujo normal.
        if change:
            return super().save_model(request, obj, form, change)

        # Alta rápida: 1 tramo por día (según turno)
        dias = sorted({int(d) for d in form.cleaned_data.get("dias_semana", [])})
        turno = form.cleaned_data.get("turno")

        if turno == "MANANA":
            inicio = APERTURA
            fin = COMIDA_INICIO
        else:
            inicio = COMIDA_FIN
            fin = CIERRE

        # Guardar el primero como el objeto "principal" que espera el admin
        obj.dia_semana = dias[0]
        obj.hora_inicio = inicio
        obj.hora_fin = fin
        super().save_model(request, obj, form, change)

        created_count = 1
        updated_count = 0

        for dia in dias[1:]:
            horario, created = HorarioPeluquero.objects.get_or_create(
                peluquero=obj.peluquero,
                dia_semana=dia,
                hora_inicio=inicio,
                hora_fin=fin,
                defaults={"activo": obj.activo},
            )
            if created:
                created_count += 1
            else:
                if horario.activo != obj.activo:
                    horario.activo = obj.activo
                    horario.save(update_fields=["activo"])
                updated_count += 1

        messages.success(
            request,
            f"Horario semanal asignado. Creados: {created_count}. Actualizados: {updated_count}.",
        )


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ("fecha", "hora", "cliente", "peluquero", "servicio", "estado")
    list_filter = ("estado", "fecha", "peluquero", "servicio")
    search_fields = (
        "cliente__nombre",
        "cliente__apellido",
        "peluquero__nombre",
        "peluquero__apellido",
        "servicio__nombre",
    )
