from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT / "desafio-2-pipeline-documentos"
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.ingest import read_pdf  # noqa: E402


def main() -> None:
    pdf_dir = PROJECT_ROOT / "data" / "raw"
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"No PDFs found in {pdf_dir}")

    extracted = 0
    ocr_backed = 0
    for pdf in pdfs[:3]:
        document = read_pdf(pdf)
        if document is None:
            raise SystemExit(f"Failed to ingest {pdf.name}")
        if not document.text.strip():
            raise SystemExit(f"Ingestion returned empty text for {pdf.name}")
        extracted += 1
        if document.ocr_used:
            ocr_backed += 1

    if extracted != 3:
        raise SystemExit(f"Expected to validate 3 PDFs, validated {extracted}")
    if ocr_backed == 0:
        raise SystemExit("OCR fallback was not exercised by the scanned dataset.")

    print("desafio-2 smoke test passed")


if __name__ == "__main__":
    main()
