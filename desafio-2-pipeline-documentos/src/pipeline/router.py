"""Roteador que direciona documentos para o extrator correto."""

import logging

from src.pipeline.extractors.base import BaseExtractor
from src.pipeline.extractors.contrato import ContratoExtractor
from src.pipeline.extractors.nota_fiscal import NotaFiscalExtractor
from src.pipeline.extractors.relatorio import RelatorioExtractor

logger = logging.getLogger(__name__)

# Mapeamento tipo -> extrator
EXTRACTOR_MAP: dict[str, type[BaseExtractor]] = {
    "nota_fiscal": NotaFiscalExtractor,
    "contrato": ContratoExtractor,
    "relatorio": RelatorioExtractor,
}


def get_extractor(doc_type: str) -> BaseExtractor:
    """Retorna o extrator adequado para o tipo de documento.

    Args:
        doc_type: Tipo do documento (nota_fiscal, contrato, relatorio).

    Returns:
        Instancia do extrator correspondente.

    Raises:
        ValueError: Se o tipo nao for suportado.
    """
    extractor_class = EXTRACTOR_MAP.get(doc_type)

    if extractor_class is None:
        supported = ", ".join(EXTRACTOR_MAP.keys())
        raise ValueError(
            f"Tipo de documento '{doc_type}' nao suportado. "
            f"Tipos validos: {supported}"
        )

    logger.debug("Roteando para extrator: %s", extractor_class.__name__)
    return extractor_class()
