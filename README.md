# Muro Entrevistador 🎙️

Aplicación en Python con Google GenAI (`google-genai`) y Gemini para practicar
entrevistas de ingeniería con IA. Carga una
oferta laboral o una plantilla; el entrevistador hace una pregunta a la vez y
adapta las siguientes a tus respuestas por audio o texto. Sirve para distintas ramas de
ingeniería, según el documento que proporciones.

## Ejecutar

Necesitas Python 3.11 o superior, conexión a Internet y una clave de
Gemini de [Google AI Studio](https://aistudio.google.com/apikey) con acceso a los
modelos configurados y cuota disponible. El micrófono es opcional si respondes por texto.

```bash
python -m venv .venv
source .venv/bin/activate
# En Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# En Windows (PowerShell): Copy-Item .env.example .env
```

Edita `.env` y coloca tu clave en `GEMINI_API_KEY`. También puedes introducirla
en la barra lateral sin crear `.env`. No publiques tu clave; `.env` está excluido
de Git. Se admite `GOOGLE_API_KEY` como alternativa; si existen ambas variables,
`GEMINI_API_KEY` tiene prioridad. Una clave introducida en la interfaz tiene
prioridad sobre ambas.

```bash
streamlit run app.py
```

En Linux y Codespaces también puedes usar `./run.sh`, que utiliza directamente
el entorno `.venv`. La apariencia y el puerto están definidos en
`.streamlit/config.toml`; no es necesario pasar opciones adicionales.

Abre `http://localhost:8501`. Si respondes por audio, permite el acceso al micrófono en el navegador.
En Codespaces, abre el puerto 8501 desde **Ports** usando la URL HTTPS y mantén
su visibilidad privada. Si alojas la app en otro equipo, el micrófono requiere
HTTPS (o localhost).

### Aviso «Invalid HTTP request received»

Este mensaje lo emite el servidor HTTP (Uvicorn) antes de ejecutar la aplicación,
cuando no puede interpretar una solicitud. Una causa es enviar tráfico HTTPS/TLS
directamente al puerto HTTP de Streamlit. Una solicitud malformada también puede
provocarlo; el mensaje por sí solo no identifica al cliente que la envió.

- En tu equipo abre **http://localhost:8501**, con `http`, sin TLS local.
- En Codespaces abre la URL **https://…-8501.app.github.dev** desde **Ports**.
  En el menú del puerto 8501, **Change Port Protocol** debe estar en **HTTP**:
  GitHub proporciona el HTTPS de la URL externa y conecta por HTTP a Streamlit.
  `.vscode/settings.json` fija esa preferencia para el proyecto; si el puerto ya
  estaba reenviado con HTTPS, cambia también la opción de la fila existente.
- Comprueba que el servidor responde con
  `curl http://localhost:8501/_stcore/health`; debe devolver `ok`.

El aviso no corresponde a la clave ni al modelo de Gemini. La aplicación conserva
los registros de errores para poder detectar otras solicitudes inválidas.
Consulta la [documentación de puertos de Codespaces](https://docs.github.com/en/codespaces/developing-in-a-codespace/forwarding-ports-in-your-codespace).

## Cómo practicar

1. Pega la oferta o carga un archivo TXT/MD en UTF-8, PDF con texto o DOCX.
   El límite es 5 MB, 20 000 caracteres y, para PDF, 40 páginas. Los PDF
   escaneados requieren OCR previo. Se leen también las tablas de los DOCX.
2. Elige dificultad, idioma (español o inglés) y entre 1 y 15 preguntas.
   Las preguntas de seguimiento cuentan para ese límite. Elige Audio o Texto como modalidad inicial.
3. Pulsa **Comenzar entrevista**. Puedes leer la pregunta o pulsar
   **Escuchar pregunta** para generar su voz con IA.
4. En **Audio**, graba tu respuesta, detén la grabación y pulsa **Transcribir respuesta**.
   Revisa y corrige la transcripción, luego pulsa **Enviar respuesta**. En **Texto**,
   escribe directamente y pulsa **Enviar respuesta**, sin usar el micrófono. Puedes
   cambiar de modalidad en cada pregunta: el borrador escrito y la transcripción
   se conservan por separado hasta enviar la respuesta.
5. Repite el ciclo. Al alcanzar el límite aparece una evaluación con fortalezas,
   aspectos a mejorar, ejemplos de respuestas y próximos pasos. Puedes terminar
   antes, después de responder al menos una pregunta.
6. Navega desde el menú lateral: **Práctica** para responder, **Historial** para
   revisar y descargar la conversación, y **Evaluación** para consultar el informe
   final. Cada opción abre una página con su propia ruta.
   **Nueva entrevista** limpia la sesión actual.

El intercambio es por turnos: debes detener y enviar cada grabación. No hay
escucha continua ni interrupciones en tiempo real. Cada audio admite hasta 14 MB
(14 MiB), para que la solicitud con el audio en base64 quede por debajo del límite
de 20 MB de Gemini. No se utiliza la Files API ni se crean archivos remotos.
Si una solicitud falla, conserva el turno y permite reintentar sin duplicar la
respuesta. Las grabaciones y borradores de turnos anteriores se liberan al avanzar.

Si el modelo está saturado, no está disponible, alcanza su límite de uso o agota
el tiempo de espera, la aplicación prueba automáticamente otro modelo compatible.
Para preguntas, evaluación y transcripción usa como alternativas
`gemini-3.5-flash-lite` y `gemini-3.1-flash-lite`; para la voz usa
`gemini-3.8-flash-lite-tts`. Conserva el historial y prefiere el modelo que funcionó
en los siguientes turnos de la sesión. Cada modelo se prueba una sola vez por
solicitud, con un tiempo de espera de 20 segundos por intento. Los errores de
clave, permisos o contenido bloqueado no activan el cambio de modelo. Si fallan
todas las alternativas, el mensaje permite reintentar y el turno no se confirma.

Las alternativas están documentadas en el [catálogo oficial de Gemini](https://ai.google.dev/gemini-api/docs/models).

## Configuración de IA

| Variable | Valor predeterminado | Uso |
| --- | --- | --- |
| `GEMINI_API_KEY` | Sin valor | Clave de Google AI Studio |
| `GOOGLE_API_KEY` | Sin valor | Alternativa a `GEMINI_API_KEY` |
| `GEMINI_CHAT_MODEL` | `gemini-3.8-flash` | Preguntas y evaluación |
| `GEMINI_TRANSCRIPTION_MODEL` | `gemini-3.8-flash` | Transcripción del audio WAV |
| `GEMINI_TTS_MODEL` | `gemini-3.8-flash-tts` | Voz opcional del entrevistador |

Para cambiar un modelo, actualiza `.env` y reinicia Streamlit. La configuración
se fija al iniciar cada entrevista. El SDK se importa con `from google import genai`
y usa Gemini Developer API mediante `client.models.generate_content`. El historial
usa los roles `user` y `model`, con las instrucciones en `system_instruction`.
La voz predeterminada es Kore y se reproduce como WAV; también se convierte PCM
a WAV si configuras un modelo TTS que devuelva audio sin cabecera. Las cuotas,
la disponibilidad y los posibles cargos dependen de tu cuenta de Google.

Documentación oficial usada: [SDK de Google GenAI](https://googleapis.github.io/python-genai/),
[audio y transcripción](https://ai.google.dev/gemini-api/docs/generate-content/audio),
[síntesis de voz](https://ai.google.dev/gemini-api/docs/generate-content/speech-generation) y
[grabación en Streamlit](https://docs.streamlit.io/develop/api-reference/widgets/st.audio_input).

## Datos y límites

Los documentos se procesan localmente y su texto se envía a Google con el
historial necesario. Las grabaciones se envían al solicitar la transcripción;
la pregunta se envía al solicitar voz. No se guardan audios ni entrevistas en
disco y no hay base de datos; recargar o perder la sesión puede borrar el avance.
La exportación incluye el texto de la oferta y la conversación, pero no la clave
ni las grabaciones. El tratamiento de datos del proveedor depende de sus políticas
y de tu cuenta de Google.

La evaluación es orientativa para practicar y puede contener errores. Esta
versión está pensada para uso personal local; no incluye autenticación para un
servicio público compartido.

## Desarrollo y pruebas

```bash
pip install -r requirements-dev.txt
pytest
ruff check .
```

Las pruebas usan respuestas de API simuladas y no necesitan clave ni generan
cargos. Comprueban lectura de documentos, límites, historial, cierre y recuperación
de errores, transcripción, síntesis de voz e interacción con la interfaz. La
captura real del micrófono y la calidad de los modelos se verifican con una sesión
manual usando una clave válida.

## Arquitectura y páginas

La interfaz usa [Streamlit Pages y Navigation](https://docs.streamlit.io/develop/api-reference/navigation/st.navigation)
con una separación MVC: el modelo mantiene la entrevista, el controlador ejecuta
las acciones y las vistas muestran formularios y resultados. `app.py` registra
las páginas y dibuja el marco compartido. Solo la página seleccionada se ejecuta.

| Página | Ruta | Uso |
| --- | --- | --- |
| Preparación | `/` | Oferta, configuración e inicio |
| Práctica | `/practica` | Pregunta actual, audio y texto |
| Historial | `/historial` | Conversación y descarga |
| Evaluación | `/evaluacion` | Informe final y descarga |

```text
app.py                              Entrada, composición y navegación
entrevistador/pages/                Páginas registradas en st.navigation
entrevistador/views/                Vistas, formularios, menú y componentes
entrevistador/controllers/          Acciones de inicio, respuesta, voz y cierre
entrevistador/interview.py           Modelo de entrevista y proveedor de IA
entrevistador/session.py             Sesión y borradores independientes de widgets
entrevistador/runtime.py             Adaptación de Session State a controladores
entrevistador/services/gemini.py     Configuración y ciclo de vida del cliente
entrevistador/documents.py           Extracción y validación de ofertas
assets/app.css                      Estilos compartidos
.streamlit/config.toml              Tema y configuración del servidor
tests/                              Pruebas sin llamadas reales a Gemini
examples/oferta_backend.md          Oferta de ejemplo
```

Los controladores y el modelo de sesión no importan Streamlit. Los borradores,
la grabación, la transcripción y la voz de la pregunta se conservan en la sesión
al navegar entre páginas. El cliente de Gemini se abre y se cierra en cada
renderizado que lo necesita; Historial y Evaluación no lo construyen. Entrar a
una página sin entrevista muestra un enlace a Preparación. Al responder la última
pregunta, la aplicación abre Evaluación automáticamente. Nueva entrevista limpia
los borradores y el contexto anterior.

La sesión sigue en memoria: cambiar de página conserva el avance, pero abrir otra
pestaña del navegador o perder la conexión de sesión puede requerir empezar de nuevo.
