#!/usr/bin/env bash
set -euo pipefail

sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-por

python -m pip install --upgrade pip uv

python scripts/materialize_assets.py

(cd desafio-1-assistente-dados && uv sync)
(cd desafio-2-pipeline-documentos && uv sync)
