# Muro · Entrevistador IA

Aplicación Django para practicar entrevistas de ingeniería adaptadas a una oferta
laboral o plantilla. Responde por texto o micrófono, revisa la conversación y recibe
una evaluación con ejemplos y próximos pasos. Utiliza Google Gemini.
La interfaz usa Bootstrap 5.3.8 con un tema oscuro y diseño adaptable a móvil,
tableta y escritorio; sus estilos se sirven desde el proyecto.

## Ejecutar manualmente

Requiere **Python 3.11 o superior**. La aplicación solo arranca al ejecutar Django
en la terminal. VS Code utiliza su configuración predeterminada, sin ajustes de
puertos personalizados en este proyecto.

Preparación inicial en Linux, macOS y Codespaces, desde la carpeta del proyecto:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
```

En Windows (PowerShell), activa el entorno con `.venv\Scripts\Activate.ps1` en
lugar de `source .venv/bin/activate`. Los demás comandos son iguales.

Para iniciar, con el entorno activado:

```bash
python manage.py runserver 0.0.0.0:8000
```

- **Local:** abre manualmente **http://localhost:8000**.
- **Codespaces:** si aparece una notificación al iniciar Django, pulsa **Open in Browser**.
  Si no aparece, usa **Ports → 8000 → globo**. Si falta la fila, agrega **8000**
  desde **Add port**. Usa protocolo **HTTP** y la dirección asignada por GitHub.

Deja la terminal abierta mientras uses Muro. **Ctrl+C** detiene el servidor y
libera el puerto. Para cerrar también el reenvío de Codespaces, usa **Stop Forwarding
Port** en la fila del puerto. No hay procesos de arranque automático.

## Configurar Gemini

La clave se configura **solo en el entorno**: copia `.env.example` a `.env` y
completa `GEMINI_API_KEY` con tu clave de Google AI Studio. Se admite
`GOOGLE_API_KEY` como alternativa. Reinicia Django si cambias `.env`.
No hay campos de claves en la interfaz ni se guardan claves de Gemini en sesiones.
No se necesita clave para abrir la aplicación; sí para comenzar una entrevista.
Necesitas acceso y cuota para los modelos configurados. Los modelos pueden cambiarse
en `.env`; el proveedor conserva las alternativas y los reintentos ya implementados.

## Dónde encontrar cada cosa

| Carpeta | Responsabilidad |
| --- | --- |
| `muro/` | Configuración general de Django y entrada de las rutas. |
| `entrevistador/domain/` | Reglas de entrevistas, documentos y estado. |
| `entrevistador/application/` | Casos de uso: comenzar, responder, transcribir y evaluar. |
| `entrevistador/integrations/` | Cliente de Gemini, configuración y modelos alternativos. |
| `entrevistador/persistence/` | Lectura y escritura de las sesiones. |
| `entrevistador/views/` | Páginas, acciones HTTP, audios y descargas. |
| `entrevistador/templates/` | HTML organizado en páginas y componentes compartidos. |
| `entrevistador/static/` | Estilos CSS y scripts JavaScript. |
| `tests/` | Pruebas unitarias, de integración y de navegador. |
| `docs/` | Guías y una oferta de ejemplo. |

Consulta el [mapa de archivos](docs/estructura.md) para saber dónde realizar cambios.
La [guía de uso](docs/uso.md) explica el flujo de la entrevista. Los comandos de pruebas
y las opciones de despliegue están en [desarrollo](docs/desarrollo.md).
