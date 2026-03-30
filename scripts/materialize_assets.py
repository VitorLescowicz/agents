from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "assets"
DB_SOURCE = ASSETS_DIR / "anexo_desafio_1.db"
DB_DEST = ROOT / "desafio-1-assistente-dados" / "data" / "clientes_completo.db"
PDF_ZIP_SOURCE = ASSETS_DIR / "anexo_desafio_2.zip"
PDF_DEST_DIR = ROOT / "desafio-2-pipeline-documentos" / "data" / "raw"


def _copy_db(force: bool) -> None:
    DB_DEST.parent.mkdir(parents=True, exist_ok=True)
    if DB_DEST.exists() and not force:
        print(f"Skipping DB copy, destination already exists: {DB_DEST}")
        return
    shutil.copy2(DB_SOURCE, DB_DEST)
    print(f"Copied database to: {DB_DEST}")


def _extract_pdfs(force: bool) -> None:
    PDF_DEST_DIR.mkdir(parents=True, exist_ok=True)
    existing_pdfs = list(PDF_DEST_DIR.glob("*.pdf"))
    if existing_pdfs and not force:
        print(f"Skipping PDF extraction, destination already has {len(existing_pdfs)} PDFs")
        return

    if force:
        for pdf in existing_pdfs:
            pdf.unlink()

    with zipfile.ZipFile(PDF_ZIP_SOURCE) as archive:
        archive.extractall(PDF_DEST_DIR)
    print(f"Extracted PDFs to: {PDF_DEST_DIR}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize challenge assets into both projects.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing extracted/copied assets.")
    args = parser.parse_args()

    if not DB_SOURCE.exists():
        raise FileNotFoundError(f"Database asset not found: {DB_SOURCE}")
    if not PDF_ZIP_SOURCE.exists():
        raise FileNotFoundError(f"PDF archive asset not found: {PDF_ZIP_SOURCE}")

    _copy_db(force=args.force)
    _extract_pdfs(force=args.force)


if __name__ == "__main__":
    main()
