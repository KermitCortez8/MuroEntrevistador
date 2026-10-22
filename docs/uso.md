# Guía de uso

## Practicar

1. Pega una oferta de 40 a 20 000 caracteres o carga TXT/MD UTF-8, PDF con texto o
   DOCX. Máximo 5 MB, 40 páginas para PDF y 20 000 caracteres de texto extraído.
   Las tablas DOCX también se leen; los PDF escaneados requieren OCR previo.
   Un archivo cargado tiene prioridad sobre el texto pegado.
2. Elige nivel, español o inglés, entre 1 y 15 preguntas y modalidad inicial.
3. Pulsa **Comenzar entrevista**. Lee la pregunta o usa **Escuchar pregunta**.
4. En Texto, escribe y envía. En Audio, permite el micrófono, graba, detén y pulsa
   **Transcribir respuesta**. Revisa el texto y envíalo. También puedes cargar WAV
   de hasta 14 MiB. El grabador limita cada toma a tres minutos y convierte a WAV
   mono a 16 kHz. El micrófono necesita un navegador moderno y localhost o HTTPS.
5. Cambia entre Texto y Audio cuando quieras; los borradores se guardan por separado.
   La interfaz indica cuándo se guardó el borrador. Detén y transcribe el audio
   antes de navegar: la grabación nueva aún no enviada existe solo en el navegador.
6. Consulta **Mi conversación** y descarga la conversación. Al completar las preguntas,
   consulta **Evaluación** o termina antes después de responder al menos una pregunta.
   La respuesta pendiente no se incluye al terminar antes.
7. **Nueva entrevista** elimina el estado, los borradores y los audios de la práctica
   actual. La configuración de `.env` no cambia.

Un fallo del proveedor conserva el turno, el texto y el audio enviado para reintentar.
Las acciones simultáneas se bloquean por sesión y los formularios de turnos antiguos
se rechazan. Las grabaciones anteriores se liberan al avanzar de pregunta.

## Datos de la sesión

La lógica de entrevistas y extracción de documentos permanece independiente de Django.
La interfaz usa plantillas HTML, CSS y JavaScript locales, sin un servicio frontend adicional.
Las [sesiones de Django](https://docs.djangoproject.com/en/5.2/topics/http/sessions/)
identifican cada navegador mediante una cookie; el contenido se guarda en el servidor.

SQLite guarda temporalmente la conversación, los borradores y los audios dentro de
`.muro/`, excluido de Git. La clave de Gemini se lee únicamente del entorno. Es almacenamiento local sin cifrado
adicional: no compartas esa carpeta. Las sesiones caducan a las 24 horas; los registros
caducados se eliminan ejecutando `python manage.py clearsessions`.
La oferta y las respuestas se envían a Google; el audio se envía al transcribir.
Las respuestas de IA son orientativas y no deciden contrataciones.

Los formularios usan [protección CSRF](https://docs.djangoproject.com/en/5.2/howto/csrf/).
El Markdown se renderiza sin HTML crudo ni enlaces con protocolos peligrosos.


## Oferta de ejemplo

Puedes practicar con [esta oferta de backend](examples/oferta_backend.md).
