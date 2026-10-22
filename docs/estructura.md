# Mapa del proyecto

Empieza en `manage.py` para ejecutar Django y en `muro/settings.py` para entender
la configuración. La aplicación de entrevistas está dentro de `entrevistador/`.

```text
MuroEntrevistador/
├── manage.py                     # Administración y arranque manual de Django
├── README.md                     # Instalación, configuración y acceso
├── .env.example                  # Variables de entorno de ejemplo
├── requirements.txt              # Dependencias de la aplicación
├── requirements-dev.txt          # Dependencias de pruebas y revisión de código
├── pyproject.toml                # Configuración de pytest y Ruff
├── muro/
│   ├── settings.py               # Entorno, SQLite, sesiones y seguridad
│   ├── urls.py                   # Incluye las rutas de la aplicación
│   ├── wsgi.py                   # Entrada para servidores WSGI
│   └── asgi.py                   # Entrada para servidores ASGI
├── entrevistador/
│   ├── urls.py                   # Direcciones y nombres de las rutas
│   ├── forms.py                  # Validación de formularios y archivos
│   ├── models.py                 # Modelo Django de la sesión de práctica
│   ├── migrations/               # Historial de cambios de la base de datos
│   ├── domain/
│   │   ├── ai.py                 # Contrato de IA, configuración y errores
│   │   ├── documents.py          # Extrae y valida ofertas TXT, MD, PDF y DOCX
│   │   ├── interview.py          # Turnos, preguntas, evaluación y exportación
│   │   └── session.py            # Estado de la entrevista y sus borradores
│   ├── application/
│   │   └── interview.py          # Coordina las acciones de la entrevista
│   ├── integrations/
│   │   └── gemini.py             # SDK de Google, voz, transcripción y alternativas
│   ├── persistence/
│   │   └── sessions.py           # Serializa el estado y coordina escrituras
│   ├── views/
│   │   ├── pages.py              # Preparación, práctica, historial y evaluación
│   │   ├── actions.py            # Formularios POST y guardado de borradores
│   │   └── media.py              # Audios privados y descargas Markdown
│   ├── templates/entrevistador/
│   │   ├── base.html             # Navegación, pie, avisos y diálogo compartido
│   │   ├── pages/                # Las cuatro pantallas de la aplicación
│   │   └── includes/empty.html   # Estado compartido sin entrevista
│   ├── static/entrevistador/
│   │   ├── css/app.css           # Estilos y adaptación a móvil
│   │   ├── vendor/bootstrap/      # Bootstrap 5.3.8 y su licencia MIT
│   │   └── js/
│   │       ├── app.js            # Borradores, formularios y controles de la interfaz
│   │       └── recorder.js       # Captura de audio en el navegador
│   └── templatetags/
│       └── formatting.py         # Renderizado seguro de Markdown
├── tests/
│   ├── factories.py              # Respuestas del SDK y WAV de prueba
│   ├── unit/                     # Entrevista, documentos y casos de uso
│   ├── integration/              # Vistas Django, sesiones y adaptador de Gemini
│   └── browser/smoke.py          # Recorrido completo con Chromium
└── docs/
    ├── estructura.md             # Este mapa
    ├── uso.md                    # Cómo practicar y cómo se manejan los datos
    ├── desarrollo.md             # Pruebas y despliegue
    └── examples/oferta_backend.md
```

Los archivos `__init__.py` identifican paquetes Python y describen su propósito.
`models.py`, `forms.py`, `urls.py`, `migrations/` y `templatetags/` conservan las
ubicaciones convencionales de Django.

## Dónde hacer un cambio

| Si quieres cambiar… | Revisa… |
| --- | --- |
| El orden o las reglas de las preguntas | `domain/interview.py` |
| La validación o lectura de una oferta | `domain/documents.py` y `forms.py` |
| Qué ocurre al enviar una respuesta | `application/interview.py` y `views/actions.py` |
| El proveedor, sus modelos o errores de API | `integrations/gemini.py` y `domain/ai.py` |
| Cómo se guardan los borradores | `persistence/sessions.py` |
| El contenido de una pantalla | `templates/entrevistador/pages/` |
| La navegación o el diálogo de confirmación | `templates/entrevistador/base.html` |
| Colores, tamaños y diseño móvil | `static/entrevistador/css/app.css` |
| Grabación, botones y guardado automático | `static/entrevistador/js/` |
| Las direcciones de las páginas | `entrevistador/urls.py` |
| Variables de entorno y base de datos | `muro/settings.py` |

Las rutas de esta tabla que empiezan por `domain/`, `application/`, `integrations/`,
`persistence/`, `views/`, `templates/` y `static/` son relativas a `entrevistador/`.

## Cómo recorre el código una respuesta

1. El navegador envía un formulario a una ruta de `entrevistador/urls.py`.
2. `views/actions.py` valida el formulario y obtiene la sesión guardada.
3. `application/interview.py` coordina la acción y llama a las reglas del dominio.
4. `domain/interview.py` solicita la siguiente pregunta o evaluación mediante el
   contrato `InterviewProvider`, implementado por `integrations/gemini.py`.
5. `persistence/sessions.py` guarda el estado; la vista redirige a la pantalla correspondiente.

El dominio no importa Django ni el SDK de Google. Esto permite comprobar sus reglas
sin servidor ni llamadas de red. Las vistas no contienen los prompts de las entrevistas.

## Archivos privados y generados

`.env` contiene la configuración privada y `.muro/` guarda SQLite y la clave local
de Django. `.venv/` es el entorno de Python. Estas ubicaciones no forman parte del
código y están excluidas de Git; no hay que moverlas para trabajar en la aplicación.
Las cachés de Python, pytest y Ruff también se regeneran automáticamente.

No renombres las migraciones existentes ni el modelo `Workspace` para ordenar
carpetas: sus nombres forman parte del historial de la base de datos.
