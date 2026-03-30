# Desafio 1 - Assistente Virtual de Dados

Assistente conversacional que transforma perguntas em linguagem natural em SQL sobre uma base SQLite e responde com visualizacao automatica.

## Arquitetura

O nucleo do sistema e um grafo LangGraph com cinco etapas:

```text
START -> discover_schema -> plan_query -> execute_sql -> synthesize_answer -> END
                                ^              |
                                |              v
                                +------- handle_error
```

Responsabilidades:

- `discover_schema`: introspeccao dinamica do banco
- `plan_query`: geracao de SQL com Gemini
- `execute_sql`: execucao read-only
- `handle_error`: tentativa de correcao de SQL
- `synthesize_answer`: resposta final e escolha de visualizacao

## Stack

- LangGraph
- langchain-google-genai
- Streamlit
- Plotly
- SQLite

## Instalacao

```bash
cd desafio-1-assistente-dados
uv sync
cp .env.example .env
```

Preencha `GOOGLE_API_KEY` no `.env`.

## Execucao

```bash
python ../scripts/materialize_assets.py
uv run app
```

## Exemplos de perguntas

1. Quais sao os 5 clientes que mais gastaram?
2. Qual a distribuicao de compras por categoria?
3. Quantos chamados de suporte foram resolvidos vs nao resolvidos?
4. Qual o ticket medio por canal de compra?
5. Quais clientes interagiram com campanhas de marketing mas nao compraram nos ultimos 3 meses?
