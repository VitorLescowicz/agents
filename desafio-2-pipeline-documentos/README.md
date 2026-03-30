# Desafio 2 - Pipeline de Documentos

Pipeline inteligente para processamento automatizado de documentos PDF utilizando LLM (Gemini Flash) para classificacao e extracao estruturada de dados.

## Descricao

Este projeto implementa um pipeline completo que:

1. **Ingere** PDFs de um diretorio, extraindo texto com PyMuPDF
2. **Classifica** cada documento em uma das 3 categorias: Nota Fiscal, Contrato ou Relatorio de Manutencao
3. **Extrai** dados estruturados de cada documento usando o extrator especializado para o tipo identificado
4. **Persiste** os resultados em JSON (agrupado por tipo) e CSV (consolidado)

## Arquitetura

```
PDF (data/raw/)
  -> Ingestao (PyMuPDF)
    -> Classificacao (Gemini Flash)
      -> Roteamento (tipo -> extrator)
        -> Extracao Estruturada (Gemini Flash + Pydantic)
          -> Persistencia (JSON/CSV)
```

### Componentes

| Modulo | Responsabilidade |
|--------|-----------------|
| `ingest.py` | Leitura de PDFs e extracao de texto bruto |
| `classify.py` | Classificacao do documento via LLM com few-shot prompting |
| `router.py` | Roteamento para o extrator correto baseado no tipo |
| `extractors/base.py` | Classe base abstrata com logica de retry e validacao |
| `extractors/nota_fiscal.py` | Extracao de campos de Notas Fiscais |
| `extractors/contrato.py` | Extracao de campos de Contratos |
| `extractors/relatorio.py` | Extracao de campos de Relatorios de Manutencao |
| `schemas.py` | Modelos Pydantic para validacao de dados |
| `persist.py` | Salvamento em JSON, CSV e log de processamento |
| `main.py` | Orquestracao do pipeline completo |

### Tipos de Documento

- **Nota Fiscal**: numero, fornecedor, CNPJ, data de emissao, itens, valor total
- **Contrato**: contratante, contratado, objeto, vigencia, valores
- **Relatorio de Manutencao**: data, tecnico, equipamento, problema, solucao, status

## Instalacao

### Pre-requisitos

- Python >= 3.11
- Chave de API do Google (Gemini)

### Setup

```bash
# Clonar o repositorio e entrar no diretorio
cd desafio-2-pipeline-documentos

# Criar e ativar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -e .

# Configurar variavel de ambiente
cp .env.example .env
# Editar .env e adicionar sua GOOGLE_API_KEY
```

## Execucao

```bash
# Colocar os PDFs em data/raw/
# Executar o pipeline
python -m src.main
```

O pipeline ira:
- Ler todos os PDFs de `data/raw/`
- Classificar e extrair dados de cada um
- Mostrar uma barra de progresso
- Salvar resultados em `output/`

## Formato de Saida

### Arquivos gerados em `output/`

| Arquivo | Descricao |
|---------|-----------|
| `notas_fiscais.json` | Dados extraidos de todas as Notas Fiscais |
| `contratos.json` | Dados extraidos de todos os Contratos |
| `relatorios.json` | Dados extraidos de todos os Relatorios |
| `resultados.csv` | Consolidado de todos os documentos |
| `processing_log.json` | Log detalhado do processamento |

### Exemplo de saida (Nota Fiscal)

```json
{
  "filename": "001_abc.pdf",
  "confidence": 0.95,
  "data": {
    "numero_nota": "001234",
    "fornecedor": "Empresa XYZ Ltda",
    "cnpj_fornecedor": "12.345.678/0001-90",
    "data_emissao": "15/03/2024",
    "itens": [
      {
        "descricao": "Parafuso M8",
        "quantidade": 100,
        "valor_unitario": 0.50,
        "valor_total": 50.00
      }
    ],
    "valor_total": 50.00
  },
  "errors": []
}
```

## Decisoes Tecnicas

1. **Gemini Flash como LLM**: escolhido pelo custo-beneficio, velocidade e boa capacidade de seguir instrucoes JSON
2. **Pydantic para validacao**: garante tipagem forte e validacao automatica dos dados extraidos
3. **Retry com feedback de erros**: se a validacao Pydantic falhar, o erro e incluido no prompt de retentativa para que o LLM corrija a saida
4. **Processamento sequencial**: evita rate limits da API do Gemini e simplifica o tratamento de erros
5. **PyMuPDF (fitz)**: biblioteca robusta e rapida para extracao de texto de PDFs
6. **Few-shot prompting na classificacao**: exemplos concretos no prompt melhoram a acuracia da classificacao
7. **Truncamento de texto**: limita o texto enviado ao LLM para evitar exceder o contexto e reduzir custos
8. **Fallback gracioso**: documentos que falham em qualquer etapa sao registrados com erros mas nao interrompem o pipeline
