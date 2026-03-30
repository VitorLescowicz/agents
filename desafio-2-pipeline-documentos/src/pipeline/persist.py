"""Modulo de persistencia: salva resultados em JSON e CSV."""

import csv
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from src.config import OUTPUT_DIR
from src.pipeline.schemas import DocumentResult

logger = logging.getLogger(__name__)


def ensure_output_dir(output_dir: Path | None = None) -> Path:
    """Garante que o diretorio de saida existe."""
    output_dir = output_dir or OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def save_results_by_type(
    results: list[DocumentResult], output_dir: Path | None = None
) -> dict[str, Path]:
    """Salva resultados agrupados por tipo em arquivos JSON separados.

    Args:
        results: Lista de DocumentResult processados.
        output_dir: Diretorio de saida. Usa OUTPUT_DIR se nao informado.

    Returns:
        Dicionario com tipo -> caminho do arquivo salvo.
    """
    output_dir = ensure_output_dir(output_dir)

    # Agrupa por tipo
    grouped: dict[str, list[dict]] = {}
    for result in results:
        doc_type = result.doc_type
        if doc_type not in grouped:
            grouped[doc_type] = []
        grouped[doc_type].append({
            "filename": result.filename,
            "confidence": result.confidence,
            "data": result.data,
            "errors": result.errors,
        })

    # Mapeamento de tipo para nome de arquivo
    type_filenames = {
        "nota_fiscal": "notas_fiscais.json",
        "contrato": "contratos.json",
        "relatorio": "relatorios.json",
    }

    saved_files: dict[str, Path] = {}
    for doc_type, items in grouped.items():
        filename = type_filenames.get(doc_type, f"{doc_type}.json")
        filepath = output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

        logger.info("Salvo %d registros em %s", len(items), filepath)
        saved_files[doc_type] = filepath

    return saved_files


def save_csv(results: list[DocumentResult], output_dir: Path | None = None) -> Path:
    """Salva resultados consolidados em CSV.

    Args:
        results: Lista de DocumentResult processados.
        output_dir: Diretorio de saida.

    Returns:
        Caminho do arquivo CSV salvo.
    """
    output_dir = ensure_output_dir(output_dir)
    filepath = output_dir / "resultados.csv"

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "filename",
            "doc_type",
            "confidence",
            "has_errors",
            "num_errors",
            "data_json",
        ])

        for result in results:
            writer.writerow([
                result.filename,
                result.doc_type,
                f"{result.confidence:.2f}",
                len(result.errors) > 0,
                len(result.errors),
                json.dumps(result.data, ensure_ascii=False),
            ])

    logger.info("CSV consolidado salvo em %s (%d linhas)", filepath, len(results))
    return filepath


def save_processing_log(
    results: list[DocumentResult],
    total_pdfs: int,
    duration_seconds: float,
    output_dir: Path | None = None,
) -> Path:
    """Salva log detalhado do processamento.

    Args:
        results: Lista de DocumentResult processados.
        total_pdfs: Numero total de PDFs encontrados.
        duration_seconds: Duracao total do processamento em segundos.
        output_dir: Diretorio de saida.

    Returns:
        Caminho do arquivo de log salvo.
    """
    output_dir = ensure_output_dir(output_dir)
    filepath = output_dir / "processing_log.json"

    # Contagem por tipo
    type_counts: dict[str, int] = {}
    error_count = 0
    for result in results:
        doc_type = result.doc_type
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        if result.errors:
            error_count += 1

    log_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_pdfs_found": total_pdfs,
            "total_processed": len(results),
            "total_with_errors": error_count,
            "total_skipped": total_pdfs - len(results),
            "duration_seconds": round(duration_seconds, 2),
        },
        "counts_by_type": type_counts,
        "files": [
            {
                "filename": r.filename,
                "doc_type": r.doc_type,
                "confidence": r.confidence,
                "status": "error" if r.errors else "success",
                "errors": r.errors,
            }
            for r in results
        ],
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

    logger.info("Log de processamento salvo em %s", filepath)
    return filepath
