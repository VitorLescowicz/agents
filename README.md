# Franq AI Engineer Challenges

Repositorio com as duas solucoes do desafio tecnico:

- `desafio-1-assistente-dados`: assistente conversacional que gera SQL sobre SQLite e responde com visualizacao.
- `desafio-2-pipeline-documentos`: pipeline de ingestao, OCR, classificacao e extracao estruturada para PDFs digitalizados.

## Estrutura

```text
.
├── anexo_desafio_1.db
├── anexo_desafio_2.zip
├── ai_engineer_pl.pdf
├── desafio-1-assistente-dados/
├── desafio-2-pipeline-documentos/
└── scripts/
```

## Setup rapido

Os assets originais ficam na raiz. Para materializar os dados dentro dos projetos:

```bash
python scripts/materialize_assets.py
```

Isso:

- copia `anexo_desafio_1.db` para `desafio-1-assistente-dados/data/clientes_completo.db`
- extrai `anexo_desafio_2.zip` para `desafio-2-pipeline-documentos/data/raw/`

## Ambiente local

### Desafio 1

```bash
cd desafio-1-assistente-dados
uv sync
cp .env.example .env
# preencher GOOGLE_API_KEY
uv run app
```

### Desafio 2

O desafio 2 agora inclui fallback de OCR com Tesseract para PDFs digitalizados.

Pre-requisitos do sistema:

- `tesseract-ocr`
- pacote de idioma `por` recomendado

```bash
cd desafio-2-pipeline-documentos
uv sync
cp .env.example .env
# preencher GOOGLE_API_KEY
uv run pipeline
```

## Smoke tests

Os checks usados no CI tambem podem ser executados localmente:

```bash
cd desafio-1-assistente-dados && uv run python ../scripts/smoke_desafio_1.py
cd ../desafio-2-pipeline-documentos && uv run python ../scripts/smoke_desafio_2.py
```

O smoke test do desafio 2 valida que o OCR consegue extrair texto do dataset digitalizado.

## GitHub Actions

O workflow em `.github/workflows/ci.yml` faz:

- instalacao das dependencias dos dois projetos
- materializacao automatica dos assets
- smoke tests do desafio 1 e do desafio 2
- job opcional de integracao com Gemini, caso o secret `GOOGLE_API_KEY` esteja configurado

## Codespaces

O devcontainer em `.devcontainer/` instala:

- Python 3.12
- `uv`
- `tesseract-ocr` e `tesseract-ocr-por`

Ao abrir o Codespace, o post-create:

- instala dependencias dos dois desafios
- materializa os assets automaticamente

## Secrets necessarios

Para execucao com Gemini em Codespaces e GitHub Actions:

- `GOOGLE_API_KEY`
