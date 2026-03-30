# Franq AI Engineer Challenges

Repositorio com os dois desafios tecnicos e os anexos originais usados para validacao local e na CI.

- `desafio-1-assistente-dados`: assistente conversacional que gera SQL sobre SQLite e responde com visualizacao.
- `desafio-2-pipeline-documentos`: pipeline de ingestao, OCR, classificacao e extracao estruturada para PDFs digitalizados.

Observacao sobre o enunciado:

- o PDF pedia a implementacao completa de apenas um desafio e a discussao arquitetural do outro
- este repositorio acabou ficando com implementacao funcional dos dois, o que excede o minimo pedido
- os READMEs de cada pasta detalham arquitetura, execucao e limites atuais

Documentacao adicional:

- `docs/ARCHITECTURE.md`: visao arquitetural consolidada para a entrevista
- `docs/DELIVERY_EVIDENCE.md`: evidencias objetivas da entrega e da validacao

## Estrutura

```text
.
├── assets/
│   ├── ai_engineer_pl.pdf
│   ├── anexo_desafio_1.db
│   └── anexo_desafio_2.zip
├── desafio-1-assistente-dados/
├── desafio-2-pipeline-documentos/
└── scripts/
```

## Setup rapido

Os anexos originais ficam em `assets/`. Para materializar os dados dentro dos projetos:

```bash
python scripts/materialize_assets.py
```

Isso:

- copia `assets/anexo_desafio_1.db` para `desafio-1-assistente-dados/data/clientes_completo.db`
- extrai `assets/anexo_desafio_2.zip` para `desafio-2-pipeline-documentos/data/raw/`

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
- unit tests dos dois desafios
- smoke tests do desafio 1 e do desafio 2
- job opcional de integracao com Gemini, caso o secret `GOOGLE_API_KEY` esteja configurado

Ultima validacao remota:

- `CI` run `#10` em `2026-03-30`: unit tests, smoke tests e integracao Gemini aprovados

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
