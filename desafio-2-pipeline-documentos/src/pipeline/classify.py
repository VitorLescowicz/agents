"""Modulo de classificacao de documentos usando LLM."""

import json
import logging
from dataclasses import dataclass

from langchain_google_genai import ChatGoogleGenerativeAI

from src.config import (
    GOOGLE_API_KEY,
    LLM_MODEL,
    LLM_RETRY_ATTEMPTS,
    LLM_RETRY_BASE_DELAY,
    LLM_RETRY_MAX_DELAY,
    LLM_TEMPERATURE,
)
from src.pipeline.llm_utils import invoke_with_retry, strip_code_fences

logger = logging.getLogger(__name__)

CLASSIFICATION_PROMPT = """Voce e um classificador de documentos. Analise o texto abaixo e classifique-o em uma das categorias:

- **nota_fiscal**: Nota Fiscal eletronica (NF-e, NFS-e). Contem numero da nota, CNPJ, itens com valores, impostos.
- **contrato**: Contrato de prestacao de servicos ou fornecimento. Contem clausulas, partes contratantes, vigencia, valores.
- **relatorio**: Relatorio de manutencao ou tecnico. Contem descricao de problema, solucao aplicada, equipamento, tecnico responsavel.

## Exemplos:

Texto: "NOTA FISCAL ELETRONICA - NF-e N. 001234 ... CNPJ: 12.345.678/0001-90 ... Item 1: Parafuso M8 ... Valor Total: R$ 1.500,00"
Classificacao: nota_fiscal

Texto: "CONTRATO DE PRESTACAO DE SERVICOS ... CONTRATANTE: Empresa ABC ... CONTRATADO: Empresa XYZ ... CLAUSULA PRIMEIRA - DO OBJETO ... Vigencia: 01/01/2024 a 31/12/2024"
Classificacao: contrato

Texto: "RELATORIO DE MANUTENCAO ... Data: 15/03/2024 ... Tecnico: Joao Silva ... Equipamento: Motor WEG W22 ... Problema: Superaquecimento ... Solucao: Troca de rolamento"
Classificacao: relatorio

## Texto do documento:

{text}

## Instrucoes:

Responda SOMENTE com um JSON valido no seguinte formato (sem markdown, sem blocos de codigo):
{{"doc_type": "<nota_fiscal|contrato|relatorio>", "confidence": <0.0 a 1.0>}}

Confidence deve refletir sua certeza na classificacao. Use valores acima de 0.8 quando o documento claramente pertence a categoria, e abaixo de 0.5 quando ha ambiguidade.
"""


@dataclass
class ClassificationResult:
    """Resultado da classificacao de um documento."""

    doc_type: str
    confidence: float


def classify_document(text: str) -> ClassificationResult:
    """Classifica um documento usando o LLM.

    Args:
        text: Texto extraido do documento.

    Returns:
        ClassificationResult com tipo e confianca.
    """
    llm = ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        google_api_key=GOOGLE_API_KEY,
    )

    # Limita o texto para evitar exceder o contexto
    truncated_text = text[:4000] if len(text) > 4000 else text

    prompt = CLASSIFICATION_PROMPT.format(text=truncated_text)
    content = ""

    try:
        response = invoke_with_retry(
            llm,
            prompt,
            max_attempts=LLM_RETRY_ATTEMPTS,
            base_delay=LLM_RETRY_BASE_DELAY,
            max_delay=LLM_RETRY_MAX_DELAY,
            logger=logger,
        )
        content = strip_code_fences(response.content)

        result = json.loads(content)
        doc_type = result.get("doc_type", "").strip().lower()
        confidence = float(result.get("confidence", 0.0))

        valid_types = {"nota_fiscal", "contrato", "relatorio"}
        if doc_type not in valid_types:
            logger.warning(
                "Tipo de documento invalido retornado pelo LLM: '%s'. Usando 'relatorio' como fallback.",
                doc_type,
            )
            doc_type = "relatorio"
            confidence = 0.3

        logger.info(
            "Documento classificado como '%s' (confianca: %.2f)",
            doc_type,
            confidence,
        )
        return ClassificationResult(doc_type=doc_type, confidence=confidence)

    except json.JSONDecodeError as e:
        logger.error("Erro ao parsear resposta do LLM: %s. Resposta: %s", e, content)
        return ClassificationResult(doc_type="relatorio", confidence=0.1)

    except Exception as e:
        logger.error("Erro na classificacao: %s", e)
        return ClassificationResult(doc_type="relatorio", confidence=0.0)
