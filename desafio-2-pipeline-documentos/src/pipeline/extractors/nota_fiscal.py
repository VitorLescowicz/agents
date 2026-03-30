"""Extrator de dados de Notas Fiscais."""

import logging
from typing import Type

from pydantic import BaseModel

from src.pipeline.extractors.base import BaseExtractor
from src.pipeline.schemas import ItemNF, NotaFiscal

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """Voce e um especialista em extracao de dados de Notas Fiscais brasileiras.

Analise o texto abaixo, extraido de uma Nota Fiscal (NF-e ou NFS-e), e extraia os seguintes campos em formato JSON:

{{
    "numero_nota": "numero da nota fiscal (string)",
    "fornecedor": "razao social do fornecedor/emissor",
    "cnpj_fornecedor": "CNPJ do fornecedor no formato XX.XXX.XXX/XXXX-XX",
    "data_emissao": "data de emissao no formato DD/MM/AAAA",
    "itens": [
        {{
            "descricao": "descricao do item",
            "quantidade": 1,
            "valor_unitario": 10.00,
            "valor_total": 10.00
        }}
    ],
    "valor_total": 0.00
}}

## Regras:
- Todos os valores monetarios devem ser numeros (float), sem "R$" ou pontos de milhar
- CNPJ deve manter a formatacao com pontos, barra e hifen
- Se um campo nao for encontrado, use string vazia "" para textos e 0.0 para numeros
- Retorne pelo menos 1 item na lista de itens
- Valor total deve ser o valor total da nota

## Texto do documento:

{text}

{error_section}

Responda SOMENTE com o JSON valido, sem markdown, sem blocos de codigo, sem explicacoes.
"""


class NotaFiscalExtractor(BaseExtractor):
    """Extrator especializado para Notas Fiscais."""

    @property
    def schema(self) -> Type[BaseModel]:
        return NotaFiscal

    @property
    def doc_type_name(self) -> str:
        return "Nota Fiscal"

    def build_prompt(self, text: str, previous_errors: list[str] | None = None) -> str:
        truncated_text = text[:6000] if len(text) > 6000 else text

        error_section = ""
        if previous_errors:
            error_section = (
                "## ATENCAO - Erros da tentativa anterior (corrija-os):\n"
                + "\n".join(f"- {e}" for e in previous_errors)
            )

        return EXTRACTION_PROMPT.format(text=truncated_text, error_section=error_section)

    def _build_empty_model(self) -> NotaFiscal:
        return NotaFiscal(
            numero_nota="",
            fornecedor="",
            cnpj_fornecedor="",
            data_emissao="",
            itens=[ItemNF(descricao="", quantidade=0, valor_unitario=0.0, valor_total=0.0)],
            valor_total=0.0,
        )
