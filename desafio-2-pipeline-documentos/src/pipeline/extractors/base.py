"""Extrator base abstrato com logica de retry e validacao."""

import json
import logging
from abc import ABC, abstractmethod
from typing import Type

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, ValidationError

from src.config import GOOGLE_API_KEY, LLM_MODEL, LLM_TEMPERATURE, MAX_RETRIES

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """Classe base para extratores de dados de documentos.

    Subclasses devem implementar `schema`, `doc_type_name` e `build_prompt`.
    A logica de chamada ao LLM, parsing JSON e retry com erros de validacao
    esta encapsulada aqui.
    """

    @property
    @abstractmethod
    def schema(self) -> Type[BaseModel]:
        """Modelo Pydantic para validacao dos dados extraidos."""
        ...

    @property
    @abstractmethod
    def doc_type_name(self) -> str:
        """Nome legivel do tipo de documento."""
        ...

    @abstractmethod
    def build_prompt(self, text: str, previous_errors: list[str] | None = None) -> str:
        """Constroi o prompt para extracao.

        Args:
            text: Texto do documento.
            previous_errors: Erros de tentativas anteriores para correcao.

        Returns:
            Prompt formatado para o LLM.
        """
        ...

    def _get_llm(self) -> ChatGoogleGenerativeAI:
        """Retorna instancia configurada do LLM."""
        return ChatGoogleGenerativeAI(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            google_api_key=GOOGLE_API_KEY,
        )

    def _parse_json_response(self, content: str) -> dict:
        """Extrai JSON da resposta do LLM, removendo markdown se necessario."""
        content = content.strip()

        # Remove blocos de codigo markdown
        if content.startswith("```"):
            content = content.split("\n", 1)[-1]
            content = content.rsplit("```", 1)[0]
        content = content.strip()

        return json.loads(content)

    def extract(self, text: str) -> tuple[BaseModel, list[str]]:
        """Extrai dados estruturados do texto do documento.

        Tenta ate MAX_RETRIES vezes, incluindo erros de validacao no prompt
        de retentativa para que o LLM corrija a saida.

        Args:
            text: Texto extraido do PDF.

        Returns:
            Tupla (modelo_validado, lista_de_erros).
            Se todas as tentativas falharem, retorna modelo com dados parciais.
        """
        llm = self._get_llm()
        errors: list[str] = []
        last_raw_data: dict = {}

        for attempt in range(1, MAX_RETRIES + 2):  # +2 para incluir tentativa inicial + retries
            previous_errors = errors if attempt > 1 else None
            prompt = self.build_prompt(text, previous_errors)

            try:
                response = llm.invoke(prompt)
                raw_data = self._parse_json_response(response.content)
                last_raw_data = raw_data

                # Valida com Pydantic
                validated = self.schema.model_validate(raw_data)
                if attempt > 1:
                    logger.info(
                        "Extracao de %s bem-sucedida na tentativa %d",
                        self.doc_type_name,
                        attempt,
                    )
                return validated, []

            except json.JSONDecodeError as e:
                error_msg = f"Tentativa {attempt}: Erro ao parsear JSON - {e}"
                logger.warning(error_msg)
                errors.append(error_msg)

            except ValidationError as e:
                error_msg = f"Tentativa {attempt}: Erro de validacao Pydantic - {e}"
                logger.warning(error_msg)
                errors.append(error_msg)

            except Exception as e:
                error_msg = f"Tentativa {attempt}: Erro inesperado - {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Todas as tentativas falharam - tenta construir modelo com dados parciais
        logger.error(
            "Todas as %d tentativas de extracao falharam para %s",
            MAX_RETRIES + 1,
            self.doc_type_name,
        )

        try:
            validated = self.schema.model_validate(last_raw_data)
            return validated, errors
        except Exception:
            # Retorna modelo com valores default/vazios
            return self._build_empty_model(), errors

    @abstractmethod
    def _build_empty_model(self) -> BaseModel:
        """Constroi modelo com valores vazios/default para fallback."""
        ...
