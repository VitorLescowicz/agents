"""Extrator de dados de Contratos."""

import logging
from typing import Type

from pydantic import BaseModel

from src.pipeline.extractors.base import BaseExtractor
from src.pipeline.schemas import Contrato

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """Voce e um especialista em extracao de dados de contratos brasileiros.

Analise o texto abaixo, extraido de um Contrato, e extraia os seguintes campos em formato JSON:

{{
    "contratante": "razao social da parte contratante",
    "contratado": "razao social da parte contratada",
    "objeto": "descricao resumida do objeto do contrato",
    "data_vigencia_inicio": "data de inicio da vigencia no formato DD/MM/AAAA",
    "data_vigencia_fim": "data de fim da vigencia no formato DD/MM/AAAA",
    "valor_mensal": null,
    "valor_total": null
}}

## Regras:
- Todos os valores monetarios devem ser numeros (float), sem "R$" ou pontos de milhar. Use null se nao encontrado.
- Datas devem estar no formato DD/MM/AAAA
- O campo "objeto" deve ser um resumo conciso (max 200 caracteres) do objeto do contrato
- Se um campo de texto nao for encontrado, use string vazia ""
- valor_mensal e valor_total podem ser null se nao informados no documento

## Texto do documento:

{text}

{error_section}

Responda SOMENTE com o JSON valido, sem markdown, sem blocos de codigo, sem explicacoes.
"""


class ContratoExtractor(BaseExtractor):
    """Extrator especializado para Contratos."""

    @property
    def schema(self) -> Type[BaseModel]:
        return Contrato

    @property
    def doc_type_name(self) -> str:
        return "Contrato"

    def build_prompt(self, text: str, previous_errors: list[str] | None = None) -> str:
        truncated_text = text[:6000] if len(text) > 6000 else text

        error_section = ""
        if previous_errors:
            error_section = (
                "## ATENCAO - Erros da tentativa anterior (corrija-os):\n"
                + "\n".join(f"- {e}" for e in previous_errors)
            )

        return EXTRACTION_PROMPT.format(text=truncated_text, error_section=error_section)

    def _build_empty_model(self) -> Contrato:
        return Contrato(
            contratante="",
            contratado="",
            objeto="",
            data_vigencia_inicio="",
            data_vigencia_fim="",
            valor_mensal=None,
            valor_total=None,
        )
