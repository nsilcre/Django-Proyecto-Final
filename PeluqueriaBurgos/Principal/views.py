from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET

from .forms import CitaForm
from .models import Cita, Cliente, Peluqueros, Servicio, get_horas_disponibles


@login_required
def principal(request):
    """Página de inicio de la peluquería (requiere login)."""
    return render(request, "principal.html")


def _get_or_create_cliente_for_user(user):
    """Obtiene (o crea) el Cliente asociado al usuario autenticado.

    Así el proyecto funciona sin tener que dar de alta el Cliente manualmente
    en el admin cada vez.
    """
    cliente, _ = Cliente.objects.get_or_create(
        user=user,
        defaults={
            "nombre": user.first_name or user.username,
            "apellido": user.last_name or "",
            "email": user.email or "",
        },
    )
    return cliente


@login_required
def reservas(request):
    """Redirige a la lista de citas del cliente.

    Más adelante se podría mostrar aquí información general.
    """
    return redirect("mis_citas")


@login_required
def mis_citas(request):
    """Listado de citas del cliente autenticado."""
    cliente = _get_or_create_cliente_for_user(request.user)
    citas = Cita.objects.filter(cliente=cliente).order_by("-fecha", "-hora")
    return render(request, "citas/mis_citas.html", {"citas": citas})


@login_required
def cita_create(request):
    """Crear una nueva cita para el cliente autenticado."""
    cliente = _get_or_create_cliente_for_user(request.user)

    if request.method == "GET":
        form = CitaForm()
        return render(request, "citas/cita_form.html", {"form": form, "titulo": "Nueva cita"})

    if request.method == "POST":
        form = CitaForm(data=request.POST)
        if form.is_valid():
            cita = form.save(commit=False)
            cita.cliente = cliente
            # Aplicar reglas de negocio del modelo (clean)
            cita.full_clean()
            cita.save()
            return redirect("mis_citas")

        return render(request, "citas/cita_form.html", {"form": form, "titulo": "Nueva cita"})


@login_required
def cita_update(request, pk=None):
    """Editar una cita del cliente autenticado.

    Solo se permite acceder si la cita pertenece al cliente.
    """
    cliente = _get_or_create_cliente_for_user(request.user)
    cita = get_object_or_404(Cita, pk=pk, cliente=cliente)

    if request.method == "GET":
        form = CitaForm(instance=cita)
        return render(request, "citas/cita_form.html", {"form": form, "titulo": "Editar cita"})

    if request.method == "POST":
        form = CitaForm(data=request.POST, instance=cita)
        if form.is_valid():
            cita = form.save(commit=False)
            # cliente ya está asignado y filtrado por seguridad
            cita.full_clean()
            cita.save()
            return redirect("mis_citas")

        return render(request, "citas/cita_form.html", {"form": form, "titulo": "Editar cita"})


@login_required
def cita_cancelar(request, pk=None):
    """Marcar una cita como cancelada.

    No se borra de la BD, solo se cambia el estado.
    """
    cliente = _get_or_create_cliente_for_user(request.user)
    cita = get_object_or_404(Cita, pk=pk, cliente=cliente)
    cita.estado = Cita.Estado.CANCELADA
    cita.save()
    return redirect("mis_citas")


@login_required
@require_GET
def api_peluqueros_por_servicio(request):
    """Devuelve peluqueros que realizan un servicio (JSON)."""
    servicio_id = request.GET.get("servicio_id")
    try:
        servicio_id_int = int(servicio_id)
    except (TypeError, ValueError):
        return JsonResponse({"error": "servicio_id inválido"}, status=400)

    peluqueros = (
        Peluqueros.objects.filter(servicios__id=servicio_id_int)
        .distinct()
        .order_by("nombre", "apellido")
    )

    return JsonResponse(
        {
            "peluqueros": [
                {"id": p.id, "nombre": f"{p.nombre} {p.apellido}".strip()}
                for p in peluqueros
            ]
        }
    )


@login_required
@require_GET
def api_horas_disponibles(request):
    """Devuelve horas disponibles (JSON) para un servicio + peluquero + fecha."""
    try:
        servicio_id = int(request.GET.get("servicio_id"))
        peluquero_id = int(request.GET.get("peluquero_id"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "servicio_id/peluquero_id inválido"}, status=400)

    fecha = parse_date(request.GET.get("fecha"))
    if not fecha:
        return JsonResponse({"error": "fecha inválida"}, status=400)

    servicio = Servicio.objects.filter(pk=servicio_id).first()
    peluquero = Peluqueros.objects.filter(pk=peluquero_id).first()
    if not servicio or not peluquero:
        return JsonResponse({"error": "servicio/peluquero no encontrado"}, status=404)

    horas = get_horas_disponibles(
        peluquero=peluquero,
        fecha=fecha,
        servicio=servicio,
    )

    return JsonResponse({"horas": [h.strftime("%H:%M") for h in horas]})
