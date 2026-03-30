"""Modulo de ingestao: leitura de PDFs e extracao de texto."""

import logging
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

from src.config import DATA_RAW_DIR, SUPPORTED_EXTENSIONS

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Representa um documento PDF lido."""

    filename: str
    text: str
    num_pages: int


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
        for page in doc:
            text_parts.append(page.get_text())
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
        return Document(filename=filepath.name, text=text, num_pages=num_pages)

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
