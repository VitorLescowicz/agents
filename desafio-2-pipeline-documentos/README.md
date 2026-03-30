# Desafio 2 - Pipeline de Documentos

Pipeline para processamento automatizado de PDFs digitalizados usando OCR + Gemini Flash para classificacao e extracao estruturada.

## Descricao

O fluxo implementado:

1. ingere PDFs de `data/raw/`
2. extrai texto com PyMuPDF
3. aplica OCR com Tesseract quando o PDF nao tem camada de texto
4. classifica o documento em `nota_fiscal`, `contrato` ou `relatorio`
5. extrai dados estruturados com validacao Pydantic
6. persiste os resultados em JSON, CSV e log de processamento

Embora o enunciado pedisse implementacao completa de apenas um desafio, este repositorio mantem este pipeline funcional para permitir validacao pratica e discussao arquitetural durante a entrevista.

## Arquitetura

```text
PDF (data/raw/)
  -> Ingestao (PyMuPDF + OCR fallback)
    -> Classificacao (Gemini Flash)
      -> Roteamento (tipo -> extrator)
        -> Extracao Estruturada (Gemini Flash + Pydantic)
          -> Persistencia (JSON/CSV)
```

## Componentes

| Modulo | Responsabilidade |
|--------|------------------|
| `ingest.py` | leitura de PDFs, extracao de texto e fallback de OCR |
| `classify.py` | classificacao do documento via LLM |
| `router.py` | roteamento para o extrator correto |
| `extractors/base.py` | retry + validacao de extracao |
| `extractors/nota_fiscal.py` | extracao de notas fiscais |
| `extractors/contrato.py` | extracao de contratos |
| `extractors/relatorio.py` | extracao de relatorios de manutencao |
| `schemas.py` | modelos Pydantic |
| `persist.py` | persistencia em JSON, CSV e log |
| `main.py` | orquestracao do pipeline |

## Requisitos

- Python >= 3.11
- `uv`
- `tesseract-ocr`
- idioma `por` do Tesseract recomendado
- `GOOGLE_API_KEY`

## Instalacao

```bash
cd desafio-2-pipeline-documentos
uv sync
cp .env.example .env
```

Variaveis relevantes em `.env`:

```env
GOOGLE_API_KEY=
LLM_MODEL=gemini-2.5-flash
LLM_RETRY_ATTEMPTS=3
LLM_RETRY_BASE_DELAY=1.5
LLM_RETRY_MAX_DELAY=8.0
OCR_ENABLED=true
OCR_LANG=por
OCR_DPI=300
TESSERACT_CMD=
```

## Execucao

```bash
python ../scripts/materialize_assets.py
uv run pipeline
```

## Saida

Arquivos gerados em `output/`:

- `notas_fiscais.json`
- `contratos.json`
- `relatorios.json`
- `resultados.csv`
- `processing_log.json`

## Justificativa da arquitetura

1. OCR com Tesseract + PyMuPDF foi escolhido em vez de depender apenas de texto embutido, porque o dataset fornecido contem PDFs digitalizados sem camada textual.
2. Classificacao e extracao separadas simplificam manutencao e reduzem erro de schema quando comparado a um unico prompt monolitico.
3. Pydantic foi usado para impor JSON estrito e alimentar retries guiados por erro, em vez de aceitar texto livre do modelo.
4. Persistencia em JSON por tipo + CSV consolidado facilita consumo operacional e auditoria sem obrigar banco adicional.
5. Processamento sequencial foi preferido nesta versao por previsibilidade de custo, simplicidade de recuperacao e menor risco de rate limit.
6. Chamadas ao Gemini usam backoff exponencial para absorver erros transientes e quota temporaria.

## Melhorias futuras

- paralelizar lotes com controle de concorrencia e backoff por quota
- adicionar benchmark de custo/latencia por etapa
- versionar prompts e schemas para reprocessamento reproduzivel
- adicionar amostragem automatica de qualidade com golden set rotulado
