"""Configuracao centralizada do pipeline de documentos."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Diretorio base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Diretorios de dados
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "output"

# Configuracao do LLM
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
LLM_MODEL = "gemini-2.0-flash"
LLM_TEMPERATURE = 0.0

# Configuracao do pipeline
MAX_RETRIES = 2
SUPPORTED_EXTENSIONS = {".pdf"}

# Tipos de documento suportados
DOC_TYPES = ["nota_fiscal", "contrato", "relatorio"]
