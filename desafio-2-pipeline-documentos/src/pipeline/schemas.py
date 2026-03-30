"""Modelos Pydantic para cada tipo de documento."""

from pydantic import BaseModel


class ItemNF(BaseModel):
    """Item individual de uma Nota Fiscal."""

    descricao: str
    quantidade: int | float
    valor_unitario: float
    valor_total: float


class NotaFiscal(BaseModel):
    """Dados extraidos de uma Nota Fiscal."""

    numero_nota: str
    fornecedor: str
    cnpj_fornecedor: str
    data_emissao: str
    itens: list[ItemNF]
    valor_total: float


class Contrato(BaseModel):
    """Dados extraidos de um Contrato."""

    contratante: str
    contratado: str
    objeto: str
    data_vigencia_inicio: str
    data_vigencia_fim: str
    valor_mensal: float | None = None
    valor_total: float | None = None


class RelatorioManutencao(BaseModel):
    """Dados extraidos de um Relatorio de Manutencao."""

    data: str
    tecnico_responsavel: str
    equipamento: str
    descricao_problema: str
    solucao_aplicada: str
    status: str = "concluido"


class DocumentResult(BaseModel):
    """Resultado consolidado do processamento de um documento."""

    filename: str
    doc_type: str
    confidence: float
    data: dict
    errors: list[str] = []
