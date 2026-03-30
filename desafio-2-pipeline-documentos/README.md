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

## Decisoes tecnicas

1. Gemini Flash para classificacao e extracao estruturada.
2. Pydantic para validar a saida e orientar retries.
3. OCR com Tesseract porque o dataset do desafio contem PDFs digitalizados sem texto embutido.
4. Processamento sequencial para reduzir rate limit e simplificar recuperacao de falhas.
5. Fallback gracioso: documentos com erro nao interrompem o restante do lote.
