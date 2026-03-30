"""Extrator de dados de Relatorios de Manutencao."""

import logging
from typing import Type

from pydantic import BaseModel

from src.pipeline.extractors.base import BaseExtractor
from src.pipeline.schemas import RelatorioManutencao

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """Voce e um especialista em extracao de dados de relatorios tecnicos e de manutencao.

Analise o texto abaixo, extraido de um Relatorio de Manutencao, e extraia os seguintes campos em formato JSON:

{{
    "data": "data do relatorio/manutencao no formato DD/MM/AAAA",
    "tecnico_responsavel": "nome do tecnico responsavel",
    "equipamento": "identificacao do equipamento (modelo, numero de serie, etc)",
    "descricao_problema": "descricao do problema encontrado",
    "solucao_aplicada": "descricao da solucao aplicada",
    "status": "concluido"
}}

## Regras:
- Data deve estar no formato DD/MM/AAAA
- O campo "status" deve ser um dos valores: "concluido", "em_andamento", "pendente". Se nao informado, use "concluido"
- descricao_problema e solucao_aplicada devem ser resumos concisos (max 300 caracteres cada)
- Se um campo nao for encontrado, use string vazia ""
- Identifique corretamente o equipamento, incluindo modelo e numero de serie se disponivel

## Texto do documento:

{text}

{error_section}

Responda SOMENTE com o JSON valido, sem markdown, sem blocos de codigo, sem explicacoes.
"""


class RelatorioExtractor(BaseExtractor):
    """Extrator especializado para Relatorios de Manutencao."""

    @property
    def schema(self) -> Type[BaseModel]:
        return RelatorioManutencao

    @property
    def doc_type_name(self) -> str:
        return "Relatorio de Manutencao"

    def build_prompt(self, text: str, previous_errors: list[str] | None = None) -> str:
        truncated_text = text[:6000] if len(text) > 6000 else text

        error_section = ""
        if previous_errors:
            error_section = (
                "## ATENCAO - Erros da tentativa anterior (corrija-os):\n"
                + "\n".join(f"- {e}" for e in previous_errors)
            )

        return EXTRACTION_PROMPT.format(text=truncated_text, error_section=error_section)

    def _build_empty_model(self) -> RelatorioManutencao:
        return RelatorioManutencao(
            data="",
            tecnico_responsavel="",
            equipamento="",
            descricao_problema="",
            solucao_aplicada="",
            status="concluido",
        )
