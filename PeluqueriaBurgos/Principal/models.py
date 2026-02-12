from datetime import date, datetime, time, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


# Reglas globales del negocio (horario de apertura/cierre)
APERTURA = time(8, 0)
CIERRE = time(21, 0)
COMIDA_INICIO = time(13, 30)
COMIDA_FIN = time(15, 0)


class Peluqueros(models.Model):
    nombre = models.CharField(
        verbose_name="Nombre",
        max_length=100,
        blank=False,
    )
    apellido = models.CharField(
        verbose_name="Apellido",
        max_length=150,
        blank=False,
    )
    servicios = models.ManyToManyField(
        "Servicio",
        related_name="peluqueros",
        verbose_name="Servicios que realiza",
        blank=True,
    )

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class Servicio(models.Model):
    nombre = models.CharField("Nombre del servicio", max_length=100)
    descripcion = models.TextField("Descripción", blank=True)
    duracion_minutos = models.PositiveIntegerField("Duración (minutos)", default=30)
    precio = models.DecimalField("Precio", max_digits=7, decimal_places=2)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"

    def __str__(self):
        return self.nombre


class Cliente(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="cliente",
        verbose_name="Usuario",
        null=True,
        blank=True,
    )
    nombre = models.CharField("Nombre", max_length=100)
    apellido = models.CharField("Apellido", max_length=150)
    telefono = models.CharField("Teléfono", max_length=20, blank=True)
    email = models.EmailField("Email", blank=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class HorarioPeluquero(models.Model):
    class DiaSemana(models.IntegerChoices):
        LUNES = 0, "Lunes"
        MARTES = 1, "Martes"
        MIERCOLES = 2, "Miércoles"
        JUEVES = 3, "Jueves"
        VIERNES = 4, "Viernes"
        SABADO = 5, "Sábado"
        DOMINGO = 6, "Domingo"

    peluquero = models.ForeignKey(
        Peluqueros,
        on_delete=models.CASCADE,
        related_name="horarios",
        verbose_name="Peluquero",
    )
    dia_semana = models.PositiveSmallIntegerField(
        "Día de la semana",
        choices=DiaSemana.choices,
    )
    hora_inicio = models.TimeField("Hora inicio")
    hora_fin = models.TimeField("Hora fin")
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Horario de peluquero"
        verbose_name_plural = "Horarios de peluqueros"
        ordering = ["peluquero", "dia_semana", "hora_inicio"]

    def __str__(self):
        return f"{self.peluquero} - {self.get_dia_semana_display()} {self.hora_inicio}-{self.hora_fin}"

    def clean(self):
        """Valida el horario de trabajo.

        Reglas:
        - Cerrado domingos.
        - Solo bloques alineados a 30 minutos.
        - Debe estar dentro de 08:00–21:00.
        - No puede solapar con el cierre de comida (13:30–15:00).
        """
        super().clean()

        if self.dia_semana == HorarioPeluquero.DiaSemana.DOMINGO:
            raise ValidationError("La peluquería cierra los domingos.")

        if not self.hora_inicio or not self.hora_fin:
            return

        if self.hora_fin <= self.hora_inicio:
            raise ValidationError("La hora fin debe ser posterior a la hora inicio.")

        # Bloques de 30 minutos
        for campo, t in (("hora_inicio", self.hora_inicio), ("hora_fin", self.hora_fin)):
            if t.second != 0 or t.microsecond != 0 or (t.minute not in (0, 30)):
                raise ValidationError(
                    {campo: "Las horas deben ir en tramos de 30 minutos (00 o 30)."}
                )

        # Dentro del horario de apertura
        if self.hora_inicio < APERTURA or self.hora_fin > CIERRE:
            raise ValidationError(
                f"El horario debe estar dentro de {APERTURA.strftime('%H:%M')}–{CIERRE.strftime('%H:%M')}"
            )

        # No solapar comida
        comida_inicio = _time_to_dt(COMIDA_INICIO)
        comida_fin = _time_to_dt(COMIDA_FIN)
        inicio = _time_to_dt(self.hora_inicio)
        fin = _time_to_dt(self.hora_fin)
        if inicio < comida_fin and comida_inicio < fin:
            raise ValidationError(
                f"La peluquería cierra de {COMIDA_INICIO.strftime('%H:%M')} a {COMIDA_FIN.strftime('%H:%M')} para comer."
            )


class TurnoPeluquero(models.Model):
    """Turnos asignados por rango de fechas (más eficiente que crear slots en BD)."""

    class Turno(models.TextChoices):
        MANANA = "MANANA", f"Mañana ({APERTURA.strftime('%H:%M')}–{COMIDA_INICIO.strftime('%H:%M')})"
        TARDE = "TARDE", f"Tarde ({COMIDA_FIN.strftime('%H:%M')}–{CIERRE.strftime('%H:%M')})"
        COMPLETO = "COMPLETO", "Completo (mañana + tarde)"

    peluquero = models.ForeignKey(
        Peluqueros,
        on_delete=models.CASCADE,
        related_name="turnos_fecha",
        verbose_name="Peluquero",
    )
    fecha_inicio = models.DateField("Fecha inicio")
    fecha_fin = models.DateField("Fecha fin")
    turno = models.CharField("Turno", max_length=10, choices=Turno.choices)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Turno por fechas"
        verbose_name_plural = "Turnos por fechas"
        indexes = [
            models.Index(fields=["peluquero", "fecha_inicio", "fecha_fin"]),
        ]
        ordering = ["-fecha_inicio", "peluquero"]

    def __str__(self):
        return f"{self.peluquero} {self.fecha_inicio}–{self.fecha_fin} ({self.get_turno_display()})"

    def clean(self):
        super().clean()
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValidationError({"fecha_fin": "La fecha fin no puede ser anterior a la fecha inicio."})


class Cita(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        REALIZADA = "REALIZADA", "Realizada"
        CANCELADA = "CANCELADA", "Cancelada"

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="citas",
        verbose_name="Cliente",
    )
    peluquero = models.ForeignKey(
        Peluqueros,
        on_delete=models.CASCADE,
        related_name="citas",
        verbose_name="Peluquero",
    )
    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.SET_NULL,
        related_name="citas",
        verbose_name="Servicio",
        null=True,
        blank=True,
    )
    fecha = models.DateField("Fecha de la cita")
    hora = models.TimeField("Hora de la cita")
    estado = models.CharField(
        "Estado",
        max_length=10,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    motivo = models.CharField("Motivo", max_length=255, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cita"
        verbose_name_plural = "Citas"
        ordering = ["-fecha", "-hora"]
        unique_together = ("peluquero", "fecha", "hora")

    def __str__(self):
        return f"Cita de {self.cliente} con {self.peluquero} el {self.fecha} a las {self.hora}"

    def clean(self):
        """Reglas de negocio de las citas.

        - Solo franjas de 30 minutos.
        - Debe caer dentro de un horario activo del peluquero.
        - No puede solapar con otras citas del mismo peluquero.
        - La fecha no puede ser anterior a hoy.
        - El peluquero debe ofrecer el servicio seleccionado.
        """
        # Fecha no pasada
        if self.fecha and self.fecha < timezone.localdate():
            raise ValidationError("La fecha de la cita no puede ser anterior a hoy.")

        # Minutos válidos: en punto o y media
        if self.hora and (self.hora.minute not in (0, 30) or self.hora.second != 0):
            raise ValidationError("Las citas solo pueden comenzar a en punto o y media.")

        # Cierre los domingos
        if self.fecha and self.fecha.weekday() == 6:
            raise ValidationError("La peluquería cierra los domingos.")

        # Cierre para comer: 13:30-15:00 (cualquier servicio que solape se rechaza)
        if self.fecha and self.hora:
            duracion = _servicio_duracion_minutos(self.servicio)
            inicio = _time_to_dt(self.hora)
            fin = inicio + timedelta(minutes=duracion)
            comida_inicio = _time_to_dt(COMIDA_INICIO)
            comida_fin = _time_to_dt(COMIDA_FIN)
            if inicio < comida_fin and comida_inicio < fin:
                raise ValidationError(
                    f"La peluquería cierra de {COMIDA_INICIO.strftime('%H:%M')} a {COMIDA_FIN.strftime('%H:%M')} para comer."
                )

        # Validar que el peluquero ofrece el servicio seleccionado
        if self.servicio_id and self.peluquero_id:
            if not self.peluquero.servicios.filter(pk=self.servicio_id).exists():
                raise ValidationError(
                    "El peluquero seleccionado no ofrece el servicio elegido."
                )

        # Validar disponibilidad real (horario + duración + no solapes)
        if self.peluquero_id and self.fecha and self.hora:
            horas_disponibles = get_horas_disponibles(
                peluquero=self.peluquero,
                fecha=self.fecha,
                servicio=self.servicio,
                exclude_cita_pk=self.pk,
            )
            if self.hora not in horas_disponibles:
                raise ValidationError("La hora seleccionada no está disponible.")


def _servicio_duracion_minutos(servicio: "Servicio | None") -> int:
    """Duración en minutos del servicio (fallback: 30)."""
    if servicio and servicio.duracion_minutos:
        return int(servicio.duracion_minutos)
    return 30


def _time_to_dt(t):
    return datetime.combine(date(2000, 1, 1), t)


def get_horas_disponibles(*, peluquero: Peluqueros, fecha, servicio=None, exclude_cita_pk=None):
    """Devuelve horas de inicio disponibles (datetime.time) para un peluquero/fecha/servicio.

    Prioridad de fuentes:
    1) TurnoPeluquero (por rango de fechas) si existe para esa fecha.
    2) HorarioPeluquero (plantilla semanal por día de la semana).

    - Paso de 30 minutos.
    - Respeta duración del servicio y evita solapes con otras citas no canceladas.
    - Regla global: cerrado domingos y de 13:30 a 15:00.
    """
    if not peluquero or not fecha:
        return []

    if fecha < timezone.localdate():
        return []

    # Cerrado domingos
    if fecha.weekday() == 6:
        return []

    duracion = _servicio_duracion_minutos(servicio)
    paso = 30

    # 1) Turno por fechas (si existe, manda sobre el semanal)
    turnos_qs = TurnoPeluquero.objects.filter(
        peluquero=peluquero,
        activo=True,
        fecha_inicio__lte=fecha,
        fecha_fin__gte=fecha,
    ).order_by("-fecha_inicio", "-id")

    intervalos_merged = []

    if turnos_qs.exists():
        turno = turnos_qs.first().turno
        if turno == TurnoPeluquero.Turno.MANANA:
            intervalos_merged = [[_time_to_dt(APERTURA), _time_to_dt(COMIDA_INICIO)]]
        elif turno == TurnoPeluquero.Turno.TARDE:
            intervalos_merged = [[_time_to_dt(COMIDA_FIN), _time_to_dt(CIERRE)]]
        else:
            intervalos_merged = [
                [_time_to_dt(APERTURA), _time_to_dt(COMIDA_INICIO)],
                [_time_to_dt(COMIDA_FIN), _time_to_dt(CIERRE)],
            ]
    else:
        # 2) Plantilla semanal
        dia_semana = fecha.weekday()
        horarios = (
            HorarioPeluquero.objects.filter(
                peluquero=peluquero,
                dia_semana=dia_semana,
                activo=True,
            )
            .order_by("hora_inicio")
        )

        if not horarios.exists():
            return []

        intervalos = []
        for h in horarios:
            inicio_h = _time_to_dt(h.hora_inicio)
            fin_h = _time_to_dt(h.hora_fin)
            if fin_h <= inicio_h:
                continue
            intervalos.append((inicio_h, fin_h))

        intervalos.sort(key=lambda x: x[0])
        for start, end in intervalos:
            if not intervalos_merged or start > intervalos_merged[-1][1]:
                intervalos_merged.append([start, end])
            else:
                intervalos_merged[-1][1] = max(intervalos_merged[-1][1], end)

    citas_qs = (
        Cita.objects.filter(
            peluquero=peluquero,
            fecha=fecha,
        )
        .exclude(estado=Cita.Estado.CANCELADA)
        .select_related("servicio")
    )
    if exclude_cita_pk:
        citas_qs = citas_qs.exclude(pk=exclude_cita_pk)

    ocupadas = []
    for cita in citas_qs:
        cita_duracion = _servicio_duracion_minutos(cita.servicio)
        inicio = _time_to_dt(cita.hora)
        fin = inicio + timedelta(minutes=cita_duracion)
        ocupadas.append((inicio, fin))

    disponibles = set()

    # Cierre para comer (13:30-15:00)
    comida_inicio = _time_to_dt(COMIDA_INICIO)
    comida_fin = _time_to_dt(COMIDA_FIN)

    for inicio_h, fin_h in intervalos_merged:
        ultimo_inicio = fin_h - timedelta(minutes=duracion)
        if ultimo_inicio < inicio_h:
            continue

        cursor = inicio_h
        # Ajustar al siguiente bloque de 30 minutos (00 o 30)
        if cursor.minute % paso != 0:
            cursor += timedelta(minutes=(paso - (cursor.minute % paso)))
        cursor = cursor.replace(second=0, microsecond=0)

        while cursor <= ultimo_inicio:
            inicio_cita = cursor
            fin_cita = cursor + timedelta(minutes=duracion)

            # No permitir citas durante el cierre de comida
            if inicio_cita < comida_fin and comida_inicio < fin_cita:
                cursor += timedelta(minutes=paso)
                continue

            solapa = False
            for o_inicio, o_fin in ocupadas:
                if inicio_cita < o_fin and o_inicio < fin_cita:
                    solapa = True
                    break

            if not solapa:
                disponibles.add(inicio_cita.time().replace(second=0, microsecond=0))

            cursor += timedelta(minutes=paso)

    return sorted(disponibles)
