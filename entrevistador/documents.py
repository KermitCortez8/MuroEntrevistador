"""Lectura local de ofertas y plantillas; no sube los archivos originales."""

from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from docx import Document
from pypdf import PdfReader

MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_CONTEXT_CHARS = 20_000


def validate_context(text: str) -> str:
    text = text.strip()
    if len(text) < 40:
        raise ValueError("Agrega una oferta o plantilla con al menos 40 caracteres.")
    if len(text) > MAX_CONTEXT_CHARS:
        raise ValueError(f"La oferta debe tener como máximo {MAX_CONTEXT_CHARS:,} caracteres.")
    return text


def extract_document(filename: str, data: bytes) -> str:
    if not data:
        raise ValueError("El archivo está vacío.")
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("El archivo supera el límite de 5 MB.")

    suffix = Path(filename).suffix.lower()
    try:
        if suffix in {".txt", ".md"}:
            text = data.decode("utf-8-sig")
        elif suffix == ".pdf":
            reader = PdfReader(BytesIO(data))
            if reader.is_encrypted:
                raise ValueError("Utiliza un PDF sin contraseña.")
            if len(reader.pages) > 40:
                raise ValueError("Utiliza un PDF de hasta 40 páginas.")
            parts = []
            for page in reader.pages:
                parts.append(page.extract_text() or "")
                if sum(len(part) for part in parts) > MAX_CONTEXT_CHARS:
                    raise ValueError("El PDF tiene demasiado texto. Carga solo la oferta laboral.")
            text = "\n".join(parts)
        elif suffix == ".docx":
            with ZipFile(BytesIO(data)) as archive:
                if sum(item.file_size for item in archive.infolist()) > 20 * 1024 * 1024:
                    raise ValueError("El documento descomprimido es demasiado grande.")
            document = Document(BytesIO(data))
            parts = [paragraph.text for paragraph in document.paragraphs]
            parts.extend(
                cell.text for table in document.tables for row in table.rows for cell in row.cells
            )
            text = "\n".join(parts)
        else:
            raise ValueError("Formato no admitido. Usa TXT, MD, PDF o DOCX.")
    except UnicodeDecodeError as exc:
        raise ValueError("Guarda el archivo de texto con codificación UTF-8.") from exc
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("No se pudo leer el documento. Comprueba que no esté dañado.") from exc

    if not text.strip():
        raise ValueError(
            "No hay texto legible. Si es un PDF escaneado, aplica OCR o pega el texto."
        )
    return validate_context(text)
