"""
URL configuration for PeluqueriaBurgos project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from Principal import views

urlpatterns = [
    # Landing: login en la raíz
    path(
        "",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    # Alias de login (por si lo necesitas explícito)
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            redirect_authenticated_user=True,
        ),
        name="login_alt",
    ),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            redirect_authenticated_user=True,
        ),
        name="login_accounts",
    ),
    # Por compatibilidad con tu URL escrita: /LoginView/
    path(
        "LoginView/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            redirect_authenticated_user=True,
        ),
        name="login_view",
    ),

    # Página principal (requiere login)
    path("inicio/", views.principal, name="home"),

    path("reservas/", views.reservas, name="reservas"),

    # Citas (zona privada del cliente)
    path("citas/", views.mis_citas, name="mis_citas"),
    path("citas/nueva/", views.cita_create, name="cita_nueva"),
    path("citas/<int:pk>/editar/", views.cita_update, name="cita_editar"),
    path("citas/<int:pk>/cancelar/", views.cita_cancelar, name="cita_cancelar"),

    # API (para selects dependientes en el formulario de cita)
    path(
        "api/peluqueros/",
        views.api_peluqueros_por_servicio,
        name="api_peluqueros_por_servicio",
    ),
    path(
        "api/horas-disponibles/",
        views.api_horas_disponibles,
        name="api_horas_disponibles",
    ),

    # Logout (volver siempre al login)
    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(next_page="login"),
        name="logout",
    ),

    path("admin/", admin.site.urls),
]
