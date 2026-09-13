"""Optional, bounded OCR for image-only public PDFs.

OCR is deliberately isolated from the normal document path.  Callers must
opt in explicitly and provide a page/time budget; a missing OCR dependency is
reported as an unsupported extraction rather than as an empty document.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Any


@dataclass(frozen=True, slots=True)
class OcrResult:
    """Sanitized OCR output and its bounded execution metadata."""

    text: str | None
    confidence: float | None
    pages_processed: int
    status: str
    warnings: tuple[str, ...] = ()


def extract_pdf_text(
    content: bytes,
    *,
    max_pages: int = 5,
    timeout_seconds: float = 30.0,
) -> OcrResult:
    """Extract text from image-only PDF bytes using optional OCR packages.

    The function never runs implicitly from :mod:`nanojuris.documents`.  It
    uses ``pypdfium2`` for rasterization and ``pytesseract`` for recognition,
    both imported lazily so the core installation stays lightweight.
    """

    if not content.startswith(b"%PDF-"):
        raise ValueError("OCR input must be a PDF byte stream")
    if not 1 <= max_pages <= 50:
        raise ValueError("max_pages must be between 1 and 50")
    if timeout_seconds <= 0 or timeout_seconds > 300:
        raise ValueError("timeout_seconds must be greater than 0 and at most 300")

    try:
        import pypdfium2 as pdfium  # type: ignore[import-not-found]
        import pytesseract  # type: ignore[import-not-found]
    except ImportError:
        return OcrResult(
            text=None,
            confidence=None,
            pages_processed=0,
            status="unsupported",
            warnings=("OCR opcional requer os extras `nanojuris[ocr]`.",),
        )

    try:
        document = pdfium.PdfDocument(content)
    except Exception as exc:  # noqa: BLE001 - parser boundary
        return OcrResult(None, None, 0, "failed", (f"Falha ao abrir PDF para OCR: {exc}",))

    page_limit = min(len(document), max_pages)
    texts: list[str] = []
    confidences: list[float] = []
    warnings: list[str] = []
    pages_processed = 0
    try:
        for index in range(page_limit):
            try:
                page = document[index]
                image = page.render(scale=2).to_pil()
                data: Any = pytesseract.image_to_data(
                    image,
                    output_type=pytesseract.Output.DICT,
                    timeout=timeout_seconds,
                )
                words = [str(value).strip() for value in data.get("text", []) if str(value).strip()]
                texts.append(" ".join(words))
                for value in data.get("conf", []):
                    try:
                        score = float(value)
                    except (TypeError, ValueError):
                        continue
                    if score >= 0:
                        confidences.append(score)
                pages_processed += 1
            except Exception as exc:  # noqa: BLE001 - page-level OCR boundary
                warnings.append(f"Falha no OCR da pagina {index + 1}: {exc}")
                break
    finally:
        close = getattr(document, "close", None)
        if callable(close):
            close()

    text = "\n\n".join(item for item in texts if item).strip() or None
    confidence = round(sum(confidences) / len(confidences), 2) if confidences else None
    status = "complete" if text else "empty"
    if pages_processed < page_limit and warnings:
        status = "partial"
    return OcrResult(text, confidence, pages_processed, status, tuple(warnings))


def extract_tiff_text(
    content: bytes,
    *,
    max_pages: int = 5,
    timeout_seconds: float = 30.0,
) -> OcrResult:
    """Extract text from a bounded TIFF image/document using optional OCR.

    Some court portals publish inteiro teor as TIFF rather than PDF.  Keep this
    path explicitly opt-in, just like PDF OCR, so an image-only source is never
    silently treated as text or as an authoritative empty result.
    """

    if not content.startswith((b"II*\x00", b"MM\x00*")):
        raise ValueError("OCR input must be a TIFF byte stream")
    if not 1 <= max_pages <= 50:
        raise ValueError("max_pages must be between 1 and 50")
    if timeout_seconds <= 0 or timeout_seconds > 300:
        raise ValueError("timeout_seconds must be greater than 0 and at most 300")

    try:
        import pytesseract  # type: ignore[import-not-found]
        from PIL import Image  # type: ignore[import-not-found]
    except ImportError:
        return OcrResult(
            text=None,
            confidence=None,
            pages_processed=0,
            status="unsupported",
            warnings=("OCR opcional requer os extras `nanojuris[ocr]`.",),
        )

    texts: list[str] = []
    confidences: list[float] = []
    warnings: list[str] = []
    pages_processed = 0
    try:
        with Image.open(BytesIO(content)) as image:
            page_limit = min(int(getattr(image, "n_frames", 1)), max_pages)
            for index in range(page_limit):
                try:
                    image.seek(index)
                    frame = image.convert("RGB")
                    data: Any = pytesseract.image_to_data(
                        frame,
                        output_type=pytesseract.Output.DICT,
                        timeout=timeout_seconds,
                    )
                    words = [
                        str(value).strip() for value in data.get("text", []) if str(value).strip()
                    ]
                    if words:
                        texts.append(" ".join(words))
                    for value in data.get("conf", []):
                        try:
                            score = float(value)
                        except (TypeError, ValueError):
                            continue
                        if score >= 0:
                            confidences.append(score)
                    pages_processed += 1
                except Exception as exc:  # noqa: BLE001 - page-level OCR boundary
                    warnings.append(f"Falha no OCR da pagina TIFF {index + 1}: {exc}")
                    break
    except Exception as exc:  # noqa: BLE001 - image parser boundary
        return OcrResult(None, None, 0, "failed", (f"Falha ao abrir TIFF para OCR: {exc}",))

    text = "\n\n".join(texts).strip() or None
    confidence = round(sum(confidences) / len(confidences), 2) if confidences else None
    status = "complete" if text else "empty"
    if warnings and pages_processed < page_limit:
        status = "partial"
    return OcrResult(text, confidence, pages_processed, status, tuple(warnings))
