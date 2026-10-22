"""Prueba opcional con Chromium y proveedor simulado: python -m tests.browser.smoke."""

import argparse
import os
import sys
import threading
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock
from wsgiref.simple_server import make_server


def main():
    parser = argparse.ArgumentParser(description="Recorre Muro con Chromium y Gemini simulado.")
    parser.add_argument(
        "--headed", action="store_true", help="Muestra Chromium en una ventana local."
    )
    parser.add_argument(
        "--video",
        type=Path,
        nargs="?",
        const=Path("artifacts/browser/flujo.webm"),
        help="Graba el recorrido en un archivo WebM.",
    )
    options = parser.parse_args()
    if options.headed and sys.platform.startswith("linux") and not os.getenv("DISPLAY"):
        parser.error("Este entorno no tiene pantalla. Usa --video para ver el recorrido grabado.")
    ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(ROOT))
    os.environ["DJANGO_SETTINGS_MODULE"] = "muro.settings"
    scratch = TemporaryDirectory(prefix="muro-browser-")
    os.environ["MURO_DATA_DIR"] = scratch.name
    os.environ["GEMINI_API_KEY"] = "test-key-not-real"
    os.environ["CODESPACE_NAME"] = ""
    import django

    django.setup()
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    from django.core.management import call_command
    from django.core.wsgi import get_wsgi_application
    from playwright.sync_api import sync_playwright

    from entrevistador.views import actions
    from tests.factories import wav_bytes

    call_command("migrate", verbosity=0)
    provider = MagicMock()
    provider.generate.side_effect = [
        "¿Cómo diseñarías una API REST?",
        "¿Cómo validarías los datos?",
        "## Evaluación\nBuen razonamiento.",
    ]
    provider.speak.return_value = wav_bytes()
    provider.transcribe.return_value = "Validaría el esquema y devolvería errores claros."

    @contextmanager
    def scope(*args):
        yield provider

    actions.provider_scope = scope
    server = make_server("127.0.0.1", 0, StaticFilesHandler(get_wsgi_application()))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    artifacts = (
        Path(os.environ["MURO_BROWSER_ARTIFACTS"]) if os.getenv("MURO_BROWSER_ARTIFACTS") else None
    )
    if artifacts:
        artifacts.mkdir(parents=True, exist_ok=True)

    def check_responsive(page, name):
        widths = (1440,) if options.headed or options.video else (320, 390, 768, 1024, 1440)
        for width in widths:
            page.set_viewport_size({"width": width, "height": 900})
            overflow = page.evaluate("""() => ({
                width: innerWidth, actual: document.documentElement.scrollWidth,
                elements: [...document.querySelectorAll('body *')].filter(el => {
                    const box = el.getBoundingClientRect();
                    return box.width > 0 && box.right > innerWidth + 1;
                }).slice(0, 6).map(el => el.tagName + '.' + el.className)
            })""")
            assert overflow["actual"] <= width + 1, (name, overflow)
            if artifacts and width in (320, 768):
                page.screenshot(path=str(artifacts / f"{name}-{width}.png"), full_page=True)
        assert page.locator("html").get_attribute("data-bs-theme") == "dark"
        assert page.locator('link[href*="bootstrap.min.css"]').count() == 1
        page.set_viewport_size({"width": 1440, "height": 1050})

    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=not options.headed,
            slow_mo=350 if options.headed or options.video else 0,
            args=[
                "--no-sandbox",
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
            ],
        )
        video_options = (
            {
                "record_video_dir": str(Path(scratch.name) / "video"),
                "record_video_size": {"width": 1440, "height": 1050},
            }
            if options.video
            else {}
        )
        context = browser.new_context(
            **video_options, permissions=["microphone"], viewport={"width": 1440, "height": 1050}
        )
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(base_url + "/")
        page.locator("#id_context").fill(
            "Ingeniero de software con experiencia en Python, PostgreSQL y diseño de APIs."
        )
        page.locator("#id_mode").select_option("Texto")
        page.locator("#id_question_limit").fill("2")
        page.get_by_role("link", name="Mi conversación", exact=True).click()
        page.wait_for_url("**/historial/")
        page.get_by_role("link", name="1 Preparar").click()
        page.wait_for_url(base_url + "/")
        assert "PostgreSQL" in page.locator("#id_context").input_value()
        assert page.locator('input[name="api_key"]').count() == 0
        check_responsive(page, "preparacion")
        if artifacts:
            page.screenshot(path=str(artifacts / "preparacion.png"), full_page=True)
        page.get_by_role("button", name="Comenzar entrevista").click()
        page.wait_for_url("**/practica/", timeout=5000)
        assert "API REST" in page.locator(".question-text").inner_text()
        check_responsive(page, "practica")
        assert page.get_by_role("button", name="Enviar respuesta").is_disabled()
        if artifacts:
            page.screenshot(path=str(artifacts / "practica.png"), full_page=True)
        page.locator("#written").fill("Usaría recursos REST y contratos explícitos.")
        page.get_by_role("link", name="Mi conversación", exact=True).click()
        page.wait_for_url("**/historial/")
        check_responsive(page, "historial")
        page.get_by_role("link", name="2 Practicar").click()
        page.wait_for_url("**/practica/")
        assert "contratos" in page.locator("#written").input_value()
        page.locator("#written").press("Control+Enter")
        page.wait_for_function(
            "document.querySelector('.question-text').textContent.includes('validarías')"
        )
        page.locator("#mode").select_option("Audio")
        page.locator("#record").click()
        page.wait_for_function(
            "document.querySelector('#record-status').textContent.includes('Grabando')"
        )
        page.locator("#mode").select_option("Texto")
        assert page.locator("#mode").input_value() == "Audio"
        page.wait_for_timeout(1100)
        page.locator("#stop-recording").click()
        page.wait_for_function("document.querySelector('#recording').files.length === 1")
        page.get_by_role("button", name="Transcribir respuesta").click()
        page.wait_for_function("document.querySelector('#transcript').value.includes('esquema')")
        page.get_by_role("button", name="Escuchar pregunta").click()
        page.wait_for_url("**/practica/?reproducir=1")
        assert page.locator('audio[src*="pregunta"]').count() == 1
        page.get_by_role("button", name="Enviar y ver evaluación").click()
        page.wait_for_url("**/evaluacion/")
        assert page.locator(".report h2").inner_text() == "Evaluación"
        check_responsive(page, "evaluacion")
        with page.expect_download() as download:
            page.get_by_role("link", name="Descargar evaluación").click()
        assert download.value.suggested_filename == "evaluacion.md"
        if artifacts:
            page.screenshot(path=str(artifacts / "evaluacion.png"), full_page=True)
        page.set_viewport_size({"width": 390, "height": 844})
        if artifacts:
            page.screenshot(path=str(artifacts / "movil.png"), full_page=True)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.get_by_role("button", name="Nueva entrevista").click()
        page.locator("#confirm-cancel").click()
        assert page.url.endswith("/evaluacion/")
        page.get_by_role("button", name="Nueva entrevista").click()
        page.locator("#confirm-accept").click()
        page.wait_for_url(base_url + "/")
        assert page.locator("#id_context").input_value() == ""
        assert not errors, errors
        assert provider.generate.call_count == 3
        assert provider.transcribe.call_count == 1
        print(
            "PASS: navegador, borradores, navegación, texto, micrófono WAV, transcripción, voz, evaluación, descarga, móvil y reinicio. Sin llamadas reales a Gemini."
        )
        context.close()
        if options.video:
            options.video.parent.mkdir(parents=True, exist_ok=True)
            page.video.save_as(str(options.video.resolve()))
            print(f"Vídeo del recorrido: {options.video.resolve()}")
        browser.close()
    server.shutdown()


if __name__ == "__main__":
    main()
