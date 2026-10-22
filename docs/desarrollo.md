# Desarrollo y despliegue

Ejecuta los comandos desde la raíz del proyecto.

Para instalar las herramientas de desarrollo y ejecutar los controles, usa el Python
del entorno `.venv` (en Windows está en `.venv\Scripts\python.exe`):

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
.venv/bin/python manage.py check
```

`python manage.py runserver 0.0.0.0:8000` inicia el servidor de desarrollo de Django.
No es un servidor de producción. Para desplegar, configura un servidor WSGI/ASGI,
HTTPS, archivos estáticos y estas variables:

- `DJANGO_DEBUG=0`
- `DJANGO_SECRET_KEY`: clave aleatoria privada y persistente.
- `DJANGO_ALLOWED_HOSTS`: dominios permitidos, separados por comas.
- `DJANGO_CSRF_TRUSTED_ORIGINS`: orígenes HTTPS permitidos, separados por comas.
- `DJANGO_SECURE_COOKIES=1`: cookies seguras con HTTPS.
- `MURO_DATA_DIR`: directorio privado de SQLite y la clave local (opcional).

Aplica `manage.py migrate`, programa `manage.py clearsessions` y sirve el resultado de
`manage.py collectstatic`. La configuración de Codespaces permite únicamente el
host correspondiente a este proyecto y el puerto 8000; no habilita todos los hosts.

Prueba opcional en navegador real (usa Gemini simulado, sin gastar cuota):

```bash
.venv/bin/python -m pip install playwright
.venv/bin/python -m playwright install chromium
.venv/bin/python -m tests.browser.smoke
```

Comprueba texto, grabación de micrófono simulado, transcripción, voz, evaluación,
descarga, borradores, navegación y vista móvil. El navegador de prueba puede
necesitar bibliotecas del sistema adicionales en Linux.

## Ejecutar un grupo de pruebas

```bash
.venv/bin/python -m pytest tests/unit -q
.venv/bin/python -m pytest tests/integration -q
```

Las pruebas unitarias cubren las reglas y casos de uso. Las de integración comprueban
Django, sesiones y el adaptador de Gemini sin consumir cuota. El recorrido de navegador
es opcional y se ejecuta por separado con un proveedor simulado. Las fábricas de
respuestas y audios compartidos están en `tests/factories.py`.

## Dependencia visual y tema

La interfaz utiliza **Bootstrap 5.3.8**, servido desde
`entrevistador/static/entrevistador/vendor/bootstrap/`. Su CSS y licencia están
incluidos; no hace falta instalar npm ni acceder a un CDN desde el navegador.
La cuadrícula, los formularios y los botones usan clases de Bootstrap.

El tema oscuro se activa con `data-bs-theme="dark"` en `base.html`. Los colores,
el contraste y los ajustes responsivos se personalizan en `css/app.css`.
Mantén los cambios de tema en ese archivo, sin editar `bootstrap.min.css`.
El recorrido de navegador comprueba las cuatro pantallas en anchos de 320, 390,
768, 1024 y 1440 píxeles.

## Ver el recorrido de Chromium

Las pruebas se ejecutan sin ventana por defecto y usan Gemini y micrófono simulados.
No necesitan una clave real ni un servidor Django iniciado previamente.

En un equipo con escritorio, puedes ver las acciones en una ventana:

```bash
python -m tests.browser.smoke --headed
```

En Codespaces, genera una grabación y abre o descarga el archivo resultante:

```bash
python -m tests.browser.smoke --video
```

El vídeo queda en `artifacts/browser/flujo.webm`, excluido de Git. Puedes indicar
una ruta diferente con `--video ruta/recorrido.webm`. Activa antes `.venv` e instala
Playwright y Chromium con los comandos de la sección de pruebas de navegador.
