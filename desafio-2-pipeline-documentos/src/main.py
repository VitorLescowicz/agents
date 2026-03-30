"""Ponto de entrada do pipeline de processamento de documentos.

Processa todos os PDFs do diretorio data/raw/, classifica cada um,
extrai dados estruturados e salva os resultados consolidados.
"""

import logging
import sys
import time
from pathlib import Path

from tqdm import tqdm

from src.config import DATA_RAW_DIR, GOOGLE_API_KEY, OUTPUT_DIR
from src.pipeline.classify import classify_document
from src.pipeline.ingest import ingest_all
from src.pipeline.persist import save_csv, save_processing_log, save_results_by_type
from src.pipeline.router import get_extractor
from src.pipeline.schemas import DocumentResult

# Configuracao de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def process_document(filename: str, text: str) -> DocumentResult:
    """Processa um unico documento pelo pipeline completo.

    Args:
        filename: Nome do arquivo PDF.
        text: Texto extraido do PDF.

    Returns:
        DocumentResult com dados extraidos e metadados.
    """
    errors: list[str] = []

    # Etapa 1: Classificacao
    try:
        classification = classify_document(text)
        doc_type = classification.doc_type
        confidence = classification.confidence
    except Exception as e:
        error_msg = f"Erro na classificacao: {e}"
        logger.error("%s - %s", filename, error_msg)
        errors.append(error_msg)
        return DocumentResult(
            filename=filename,
            doc_type="desconhecido",
            confidence=0.0,
            data={},
            errors=errors,
        )

    # Etapa 2: Roteamento e extracao
    try:
        extractor = get_extractor(doc_type)
        extracted_data, extraction_errors = extractor.extract(text)
        errors.extend(extraction_errors)
        data = extracted_data.model_dump()
    except Exception as e:
        error_msg = f"Erro na extracao: {e}"
        logger.error("%s - %s", filename, error_msg)
        errors.append(error_msg)
        data = {}

    return DocumentResult(
        filename=filename,
        doc_type=doc_type,
        confidence=confidence,
        data=data,
        errors=errors,
    )


def main(data_dir: Path | None = None, output_dir: Path | None = None) -> None:
    """Executa o pipeline completo de processamento de documentos.

    Args:
        data_dir: Diretorio com PDFs. Usa DATA_RAW_DIR se nao informado.
        output_dir: Diretorio de saida. Usa OUTPUT_DIR se nao informado.
    """
    data_dir = data_dir or DATA_RAW_DIR
    output_dir = output_dir or OUTPUT_DIR

    logger.info("=" * 60)
    logger.info("Pipeline de Documentos - Inicio")
    logger.info("=" * 60)
    logger.info("Diretorio de entrada: %s", data_dir)
    logger.info("Diretorio de saida: %s", output_dir)

    # Validacao da API key
    if not GOOGLE_API_KEY:
        logger.error(
            "GOOGLE_API_KEY nao configurada. "
            "Crie um arquivo .env com GOOGLE_API_KEY=sua_chave"
        )
        sys.exit(1)

    start_time = time.time()

    # Etapa 1: Ingestao
    logger.info("-" * 40)
    logger.info("Etapa 1: Ingestao de PDFs")
    documents = ingest_all(data_dir)

    if not documents:
        logger.warning("Nenhum documento para processar. Encerrando.")
        return

    total_pdfs = len(list(data_dir.glob("*.pdf")))

    # Etapa 2: Processamento sequencial
    logger.info("-" * 40)
    logger.info("Etapa 2: Classificacao e Extracao")
    results: list[DocumentResult] = []

    for doc in tqdm(documents, desc="Processando documentos", unit="doc"):
        result = process_document(doc.filename, doc.text)
        results.append(result)

    # Etapa 3: Persistencia
    logger.info("-" * 40)
    logger.info("Etapa 3: Salvando resultados")
    output_dir.mkdir(parents=True, exist_ok=True)

    save_results_by_type(results, output_dir)
    save_csv(results, output_dir)

    duration = time.time() - start_time
    save_processing_log(results, total_pdfs, duration, output_dir)

    # Resumo final
    type_counts: dict[str, int] = {}
    error_count = 0
    for r in results:
        type_counts[r.doc_type] = type_counts.get(r.doc_type, 0) + 1
        if r.errors:
            error_count += 1

    logger.info("=" * 60)
    logger.info("RESUMO DO PROCESSAMENTO")
    logger.info("=" * 60)
    logger.info("Total de PDFs encontrados: %d", total_pdfs)
    logger.info("Total processados com sucesso: %d", len(results))
    logger.info("Total com erros: %d", error_count)
    logger.info("Distribuicao por tipo:")
    for doc_type, count in sorted(type_counts.items()):
        logger.info("  - %s: %d", doc_type, count)
    logger.info("Tempo total: %.1f segundos", duration)
    logger.info("Resultados salvos em: %s", output_dir)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
