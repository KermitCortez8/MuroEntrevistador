# Muro Entrevistador 🎙️

Aplicación en Python para practicar entrevistas de ingeniería con IA. Carga una
oferta laboral o una plantilla; el entrevistador hace una pregunta a la vez y
adapta las siguientes a tus respuestas por audio. Sirve para distintas ramas de
ingeniería, según el documento que proporciones.

## Ejecutar

Necesitas Python 3.11 o superior, conexión a Internet, un micrófono y una clave de
OpenAI con acceso a los modelos configurados y saldo de API.

```bash
python -m venv .venv
source .venv/bin/activate
# En Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# En Windows (PowerShell): Copy-Item .env.example .env
```

Edita `.env` y coloca tu clave en `OPENAI_API_KEY`. También puedes introducirla
en la barra lateral sin crear `.env`. No publiques tu clave; `.env` está excluido
de Git.

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
escucha continua ni interrupciones en tiempo real. Cada audio admite hasta 24 MB.
Si una solicitud falla, conserva el turno y permite reintentar sin duplicar la
respuesta. Las grabaciones y borradores de turnos anteriores se liberan al avanzar.

## Configuración de IA

| Variable | Valor predeterminado | Uso |
| --- | --- | --- |
| `OPENAI_API_KEY` | Sin valor | Credencial de API |
| `OPENAI_CHAT_MODEL` | `gpt-4.1-mini` | Preguntas y evaluación con Responses API |
| `OPENAI_TRANSCRIPTION_MODEL` | `gpt-4o-mini-transcribe` | Audio a texto |
| `OPENAI_TTS_MODEL` | `gpt-4o-mini-tts` | Voz opcional del entrevistador |

Para cambiar un modelo, actualiza `.env` y reinicia Streamlit. La configuración
se fija al iniciar cada entrevista. Los cargos y el acceso dependen de tu cuenta
de API; una suscripción a ChatGPT no configura esta aplicación.

Documentación oficial usada: [generación de texto](https://developers.openai.com/api/docs/guides/text),
[transcripción](https://developers.openai.com/api/docs/guides/speech-to-text),
[síntesis de voz](https://developers.openai.com/api/docs/guides/text-to-speech) y
[grabación en Streamlit](https://docs.streamlit.io/develop/api-reference/widgets/st.audio_input).

## Datos y límites

Los documentos se procesan localmente y su texto se envía a OpenAI con el
historial necesario. Las grabaciones se envían al solicitar la transcripción;
la pregunta se envía al solicitar voz. No se guardan audios ni entrevistas en
disco y no hay base de datos; recargar o perder la sesión puede borrar el avance.
La exportación incluye el texto de la oferta y la conversación, pero no la clave
ni las grabaciones. Las llamadas de texto usan `store=False`; el tratamiento de
datos del proveedor depende de su política y tu cuenta.

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
tests/                       Pruebas sin llamadas reales a OpenAI
examples/oferta_backend.md   Oferta de ejemplo para empezar
```
