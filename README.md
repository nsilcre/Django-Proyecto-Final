# ✂️ Peluquería Burgos

![Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Django](https://img.shields.io/badge/Django-5.2-green.svg)
![Bootstrap](https://img.shields.io/badge/Design-Premium-gold)

> **Sistema integral de gestión de citas para peluquerías.**
> Elegancia y eficiencia en una sola plataforma.

## 📋 Descripción

**Peluquería Burgos** es una aplicación web moderna diseñada para optimizar la reserva de citas y la gestión operativa de una peluquería. Con un diseño **"Black & Gold"** premium, ofrece una experiencia de usuario sofisticada y una herramienta administrativa potente.

El sistema permite a los clientes reservar citas en tiempo real, validando automáticamente la disponibilidad de los estilistas, respetando turnos, horarios de comida y días festivos.

## ✨ Características Principales

### 🧑‍💻 Para el Cliente
*   **Diseño Premium**: Interfaz oscura y elegante, totalmente responsive.
*   **Reserva Inteligente**: Asistente paso a paso para elegir servicio, profesional y hora.
*   **Disponibilidad Real**: Cálculo automático de huecos libres (30 min) evitando solapes.
*   **Gestión Personal**: Panel "Mis Citas" para consultar historial y cancelar reservas pendientes.

### 🏢 Para la Administración
*   **Gestión de Profesionales**: Alta de peluqueros y asignación de servicios especializados.
*   **Control de Horarios**:
    *   Plantillas semanales (Lunes-Sábado).
    *   **Turnos por Fechas**: Asignación masiva de turnos (Mañana/Tarde/Completo) para periodos específicos.
*   **Reglas de Negocio Automatizadas**:
    *   Cierre automático domingos.
    *   Bloqueo de hora de comida (13:30 - 15:00).
    *   Validación de duplicidad de citas.

## 🛠️ Tecnologías

Este proyecto está construido con un stack robusto y moderno:

*   **Backend**: Python, Django 5.2
*   **Frontend**: HTML5, CSS3 (Custom Variables), JavaScript Vanilla, Bootstrap 5.3
*   **Base de Datos**: SQLite (Dev), extensible a PostgreSQL
*   **Seguridad**: Autenticación Django, Validadores de contraseña personalizados

## 🚀 Instalación y Puesta en Marcha

Sigue estos pasos para ejecutar el proyecto en tu entorno local:

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/tu-usuario/peluqueria-burgos.git
    cd peluqueria-burgos
    ```

2.  **Crear entorno virtual:**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar base de datos:**
    ```bash
    cd PeluqueriaBurgos
    python manage.py migrate
    ```

5.  **Crear superusuario (Administrador):**
    ```bash
    python manage.py createsuperuser
    ```

6.  **Iniciar servidor:**
    ```bash
    python manage.py runserver
    ```

7.  **Acceder:** Aboe tu navegador en `http://127.0.0.1:8000/`

## 🧪 Usuarios de Prueba

Para facilitar las pruebas, puedes usar el script de creación de usuario o los siguientes datos si ya los has generado:

*   **Usuario**: `GertrudisMena`
*   **Contraseña**: `GertrudisMena`

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.

---
*Desarrollado con ❤️ como Proyecto Final de DAW.*
