# MuroEntrevistador

Aplicación web mínima de práctica de entrevistas para **Ingeniería Informática**.

## ¿Qué hace?

- Recibe una **plantilla u oferta laboral**.
- Genera preguntas técnicas relacionadas (backend, frontend, bases de datos, cloud, testing, algoritmos y seguridad).
- Funciona como entrevistador en flujo iterativo: pregunta → respuesta → siguiente pregunta.
- Permite responder con **audio** usando reconocimiento de voz del navegador.

## Cómo usar

1. Abre `/home/runner/work/MuroEntrevistador/MuroEntrevistador/index.html` en un navegador moderno.
2. Pega la oferta/plantilla del puesto.
3. Pulsa **Iniciar entrevista**.
4. Para responder por voz, usa **🎙️ Responder con audio** y concede permisos de micrófono.
5. Revisa y edita la transcripción si quieres, luego envía la respuesta para continuar.

## Notas

- El reconocimiento de voz depende de la compatibilidad del navegador (Web Speech API).
- Se usa síntesis de voz para leer las preguntas cuando está disponible.
