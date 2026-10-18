# Muro Entrevistador 🎙️

Aplicación en Python con Google GenAI (`google-genai`) y Gemini para practicar
entrevistas de ingeniería con IA. Carga una
oferta laboral o una plantilla; el entrevistador hace una pregunta a la vez y
adapta las siguientes a tus respuestas por audio. Sirve para distintas ramas de
ingeniería, según el documento que proporciones.

## Ejecutar

Necesitas Python 3.11 o superior, conexión a Internet, un micrófono y una clave de
Gemini de [Google AI Studio](https://aistudio.google.com/apikey) con acceso a los
modelos configurados y cuota disponible.

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

Abre `http://localhost:8501` y permite el acceso al micrófono en el navegador.
En Codespaces, abre el puerto 8501 desde **Ports** usando la URL HTTPS y mantén
su visibilidad privada. Si alojas la app en otro equipo, el micrófono requiere
HTTPS (o localhost).

## Cómo practicar

1. Pega la oferta o carga un archivo TXT/MD en UTF-8, PDF con texto o DOCX.
   El límite es 5 MB, 20 000 caracteres y, para PDF, 40 páginas. Los PDF
   escaneados requieren OCR previo. Se leen también las tablas de los DOCX.
2. Elige dificultad, idioma (español o inglés) y entre 1 y 15 preguntas.
   Las preguntas de seguimiento cuentan para ese límite.
3. Pulsa **Comenzar entrevista**. Puedes leer la pregunta o pulsar
   **Escuchar pregunta** para generar su voz con IA.
4. Graba tu respuesta, detén la grabación y pulsa **Transcribir respuesta**.
   Revisa y corrige la transcripción, luego pulsa **Enviar respuesta**.
5. Repite el ciclo. Al alcanzar el límite aparece una evaluación con fortalezas,
   aspectos a mejorar, ejemplos de respuestas y próximos pasos. Puedes terminar
   antes, después de responder al menos una pregunta.
6. Descarga la conversación y evaluación en Markdown. **Nueva entrevista**
   limpia la sesión actual.

El intercambio es por turnos: debes detener y enviar cada grabación. No hay
escucha continua ni interrupciones en tiempo real. Cada audio admite hasta 14 MB
(14 MiB), para que la solicitud con el audio en base64 quede por debajo del límite
de 20 MB de Gemini. No se utiliza la Files API ni se crean archivos remotos.
Si una solicitud falla, conserva el turno y permite reintentar sin duplicar la
respuesta. Las grabaciones y borradores de turnos anteriores se liberan al avanzar.

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

```text
app.py                       Interfaz Streamlit y grabación
entrevistador/documents.py    Extracción y validación de ofertas
entrevistador/interview.py    Proveedor de IA, historial y evaluación
tests/                       Pruebas sin llamadas reales a Gemini
examples/oferta_backend.md   Oferta de ejemplo para empezar
```
