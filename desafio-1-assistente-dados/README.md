# Desafio 1 - Assistente Virtual de Dados

Assistente conversacional que transforma perguntas em linguagem natural em SQL sobre uma base SQLite e responde com visualizacao automatica.

## Arquitetura

O nucleo do sistema e um grafo LangGraph com sete etapas:

```text
START -> discover_schema -> analyze_question -> plan_query -> execute_sql
                                               ^              |
                                               |              v
                                  advance_plan <- handle_error
                                               |
                                               v
                                        synthesize_answer -> END
```

Responsabilidades:

- `discover_schema`: introspeccao dinamica do banco
- `analyze_question`: cria um plano explicito com ate 3 etapas
- `plan_query`: geracao de SQL com Gemini para a etapa corrente
- `execute_sql`: execucao read-only
- `handle_error`: tentativa de correcao de SQL
- `advance_plan`: consolida os achados intermediarios
- `synthesize_answer`: resposta final e escolha de visualizacao

## Transparencia da resposta

O frontend mostra:

- resposta em linguagem natural
- plano de analise com etapas explicitas
- historico das SQLs tentadas
- trilha de execucao com retries, erros e achados intermediarios
- visualizacao dinamica coerente com o resultado

Isso cobre o requisito de expor como a resposta foi produzida com mais detalhe do que a query final isolada.

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

Preencha `GOOGLE_API_KEY` no `.env`. O modelo default esta em `LLM_MODEL=gemini-2.5-flash`.

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

## Consultas testadas

Estas consultas foram validadas durante o desenvolvimento e/ou na CI:

1. Quais sao os 3 clientes que mais gastaram?
2. Qual a distribuicao de compras por categoria?
3. Quantos chamados de suporte foram resolvidos vs nao resolvidos?
4. Qual o ticket medio por canal de compra?
5. Liste os 5 estados com maior numero de clientes que compraram via app.

## Testes automatizados

- unit tests para parsing de respostas, limpeza de SQL e normalizacao do plano
- smoke test para introspeccao do schema, execucao SQLite e heuristica de graficos
- integracao com Gemini na CI quando `GOOGLE_API_KEY` esta configurada
- backoff exponencial para falhas transientes ou quota temporaria do LLM

## Melhorias e extensoes

- incluir avaliacao automatizada com suite de perguntas esperadas e verificacao semantica
- adicionar cache de schema e resultados para reduzir latencia e custo
- suportar selecao manual de visualizacao pelo usuario quando houver ambiguidade
- adicionar memoria conversacional entre perguntas do mesmo usuario
