"""Modulo de ingestao: leitura de PDFs e extracao de texto."""

import io
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

from src.config import (
    DATA_RAW_DIR,
    OCR_DPI,
    OCR_ENABLED,
    OCR_LANG,
    SUPPORTED_EXTENSIONS,
    TESSERACT_CMD,
)

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Representa um documento PDF lido."""

    filename: str
    text: str
    num_pages: int
    ocr_used: bool = False
    ocr_pages: int = 0


@lru_cache(maxsize=1)
def _ocr_available() -> bool:
    """Valida se o fallback de OCR esta disponivel no ambiente."""
    if not OCR_ENABLED:
        logger.info("OCR desabilitado por configuracao.")
        return False

    if TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception as exc:
        logger.warning("OCR indisponivel no ambiente atual: %s", exc)
        return False


def _ocr_page(page: fitz.Page) -> str:
    """Renderiza uma pagina como imagem e aplica OCR."""
    matrix = fitz.Matrix(OCR_DPI / 72, OCR_DPI / 72)
    pixmap = page.get_pixmap(matrix=matrix, alpha=False)
    image = Image.open(io.BytesIO(pixmap.tobytes("png")))
    return pytesseract.image_to_string(image, lang=OCR_LANG).strip()


def read_pdf(filepath: Path) -> Document | None:
    """Le um arquivo PDF e extrai seu texto.

    Args:
        filepath: Caminho para o arquivo PDF.

    Returns:
        Document com texto extraido ou None se houver erro.
    """
    try:
        doc = fitz.open(str(filepath))
        text_parts: list[str] = []
        ocr_used = False
        ocr_pages = 0

        for page in doc:
            page_text = page.get_text("text").strip()
            if not page_text and _ocr_available():
                page_text = _ocr_page(page)
                if page_text:
                    ocr_used = True
                    ocr_pages += 1

            if page_text:
                text_parts.append(page_text)
        text = "\n".join(text_parts)
        num_pages = len(doc)
        doc.close()

        if not text.strip():
            logger.warning("PDF sem texto extraivel: %s", filepath.name)
            return None

        logger.info(
            "PDF lido com sucesso: %s (%d paginas, %d caracteres)",
            filepath.name,
            num_pages,
            len(text),
        )
        if ocr_used:
            logger.info(
                "OCR utilizado em %s (%d de %d paginas)",
                filepath.name,
                ocr_pages,
                num_pages,
            )
        return Document(
            filename=filepath.name,
            text=text,
            num_pages=num_pages,
            ocr_used=ocr_used,
            ocr_pages=ocr_pages,
        )

    except Exception as e:
        logger.warning("Erro ao ler PDF '%s': %s", filepath.name, e)
        return None


def ingest_all(data_dir: Path | None = None) -> list[Document]:
    """Le todos os PDFs de um diretorio.

    Args:
        data_dir: Diretorio com os PDFs. Usa DATA_RAW_DIR se nao informado.

    Returns:
        Lista de Documents lidos com sucesso.
    """
    data_dir = data_dir or DATA_RAW_DIR
    if not data_dir.exists():
        logger.error("Diretorio de dados nao encontrado: %s", data_dir)
        return []

    pdf_files = sorted(
        f for f in data_dir.iterdir() if f.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not pdf_files:
        logger.warning("Nenhum PDF encontrado em: %s", data_dir)
        return []

    logger.info("Encontrados %d PDFs em %s", len(pdf_files), data_dir)

    documents: list[Document] = []
    for filepath in pdf_files:
        doc = read_pdf(filepath)
        if doc is not None:
            documents.append(doc)

    logger.info(
        "Ingestao concluida: %d/%d PDFs lidos com sucesso",
        len(documents),
        len(pdf_files),
    )
    return documents
