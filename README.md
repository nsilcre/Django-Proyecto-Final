# Peluquería Burgos

Sistema de gestión de citas para peluquería desarrollado con Django.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Django](https://img.shields.io/badge/Django-5.2-green.svg)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Descripción

Aplicación web que permite a los clientes de una peluquería gestionar sus citas de forma sencilla. El sistema incluye:

- **Reserva de citas**: Selección de servicio, peluquero, fecha y hora disponible
- **Gestión de citas**: Visualización, edición y cancelación de reservas
- **Panel de administración**: Gestión completa de peluqueros, servicios, horarios y turnos
- **Validación de disponibilidad**: Cálculo automático de horas libres según horarios y citas existentes

## Características

- Autenticación de usuarios con validación de contraseñas
- Horarios flexibles por peluquero (plantilla semanal + turnos por fechas)
- API interna para selección dinámica de peluqueros y horas
- Reglas de negocio configurables (horario de apertura, cierre por comida, días festivos)
- Interfaz responsive con Bootstrap 5

## Requisitos

- Python 3.10 o superior
- Django 5.2+

## Instalación

1. **Clonar el repositorio**

```bash
git clone https://github.com/tu-usuario/peluqueria-burgos.git
cd peluqueria-burgos
```

2. **Crear y activar entorno virtual**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

3. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

4. **Aplicar migraciones**

```bash
cd PeluqueriaBurgos
python manage.py migrate
```

5. **Crear superusuario**

```bash
python manage.py createsuperuser
```

6. **Ejecutar servidor de desarrollo**

```bash
python manage.py runserver
```

7. Acceder a `http://127.0.0.1:8000/`

## Estructura del Proyecto

```
PeluqueriaBurgos/
├── PeluqueriaBurgos/          # Configuración del proyecto
│   ├── settings.py
│   ├── urls.py
│   ├── password_validators.py
│   └── wsgi.py
├── Principal/                  # Aplicación principal
│   ├── models.py              # Modelos: Peluquero, Servicio, Cliente, Cita...
│   ├── views.py               # Vistas y API endpoints
│   ├── forms.py               # Formularios
│   ├── admin.py               # Configuración del panel admin
│   └── static/css/            # Estilos personalizados
├── templates/                  # Plantillas HTML
│   ├── base.html
│   ├── principal.html
│   ├── registration/
│   └── citas/
└── manage.py
```

## Modelos Principales

| Modelo | Descripción |
|--------|-------------|
| `Peluqueros` | Profesionales con servicios asignados |
| `Servicio` | Servicios ofrecidos con duración y precio |
| `Cliente` | Clientes vinculados a usuarios del sistema |
| `HorarioPeluquero` | Plantilla de horario semanal por peluquero |
| `TurnoPeluquero` | Turnos específicos por rango de fechas |
| `Cita` | Reservas con fecha, hora, servicio y estado |

## Reglas de Negocio

- **Horario**: 08:00 - 21:00
- **Cierre por comida**: 13:30 - 15:00
- **Domingos**: Cerrado
- **Bloques de cita**: 30 minutos
- **Contraseñas**: Mínimo 6 caracteres, al menos una mayúscula

## API Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/peluqueros/` | GET | Peluqueros por servicio |
| `/api/horas-disponibles/` | GET | Horas libres por peluquero/fecha |

## Uso del Panel de Administración

1. Acceder a `/admin/` con credenciales de superusuario
2. Configurar servicios disponibles
3. Añadir peluqueros y asignarles servicios
4. Establecer horarios semanales o turnos por fechas
5. Gestionar citas y clientes

## Tecnologías Utilizadas

- **Backend**: Django 5.2, Python 3.10+
- **Frontend**: HTML5, CSS3, JavaScript (vanilla)
- **Framework CSS**: Bootstrap 5.3
- **Base de datos**: SQLite (desarrollo)

## Licencia

Este proyecto está bajo la Licencia MIT.

## Autor

Desarrollado como proyecto final de DAW.
