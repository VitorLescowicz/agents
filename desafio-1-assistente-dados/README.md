# Desafio 1 — Assistente Virtual de Dados

Assistente conversacional que transforma perguntas em linguagem natural em consultas SQL, executa-as sobre uma base SQLite de clientes e retorna respostas com visualizacoes automaticas.

## Arquitetura

O nucleo do sistema e um **agente LangGraph** com 5 nos:

```
START -> discover_schema -> plan_query -> execute_sql -> synthesize_answer -> END
                                ^              |
                                |        (erro + retries < 3)
                                |              v
                                +------- handle_error
```

| No | Responsabilidade |
|----|-----------------|
| `discover_schema` | Introspecta o banco via `PRAGMA table_info` e `sqlite_master`, cacheia o schema no state |
| `plan_query` | Envia pergunta + schema para o Gemini 2.0 Flash gerar SQL |
| `execute_sql` | Executa a query em modo read-only; captura erros |
| `handle_error` | Se houve erro, envia query + mensagem de erro para o LLM corrigir (max 3 tentativas) |
| `synthesize_answer` | Gera resposta em linguagem natural e sugere tipo de visualizacao |

### Stack

- **LLM**: Google Gemini 2.0 Flash (`langchain-google-genai`)
- **Orquestrador**: LangGraph (state machine com edges condicionais)
- **Frontend**: Streamlit com chat interface
- **Visualizacao**: Plotly Express (bar, line) + st.metric + st.dataframe
- **Banco**: SQLite (conexao read-only via URI)

## Banco de dados

| Tabela | Registros | Descricao |
|--------|-----------|-----------|
| `clientes` | 100 | Dados cadastrais e valor total gasto |
| `compras` | 946 | Historico de compras por categoria e canal |
| `suporte` | 273 | Chamados de suporte tecnico |
| `campanhas_marketing` | 248 | Interacoes com campanhas |

## Instalacao

```bash
# 1. Clone o repositorio e entre no diretorio
cd desafio-1-assistente-dados

# 2. Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows

# 3. Instale as dependencias
pip install -e .

# 4. Configure a API key
cp .env.example .env
# Edite .env e insira sua GOOGLE_API_KEY

# 5. Execute
streamlit run src/app.py
```

## Perguntas de exemplo

1. **"Quais sao os 5 clientes que mais gastaram?"**
2. **"Qual a distribuicao de compras por categoria?"**
3. **"Quantos chamados de suporte foram resolvidos vs nao resolvidos?"**
4. **"Qual o ticket medio por canal de compra?"**
5. **"Quais clientes interagiram com campanhas de marketing mas nao compraram nos ultimos 3 meses?"**

## Decisoes tecnicas

### Por que LangGraph e nao LangChain Agent?
LangGraph oferece controle explicito sobre o fluxo: edges condicionais para retry, separacao clara entre geracao SQL e sintese de resposta, e facilidade de debug via state visivel.

### Por que Gemini 2.0 Flash?
Modelo rapido, barato e com boa capacidade de SQL generation. O modelo Flash atende o requisito de latencia para uma UX conversacional.

### Por que heuristica para visualizacao?
Usar o LLM para escolher o tipo de grafico adiciona latencia sem ganho significativo. Regras simples (1 valor → metric, data+numero → line, categoria+numero → bar) cobrem >90% dos casos.

### Conexao read-only
O banco e aberto com `?mode=ro` para garantir que nenhuma query acidental modifique dados.

### Retry com correcao de SQL
Erros de SQL sao capturados e enviados de volta ao LLM com a mensagem de erro, permitindo auto-correcao em ate 3 tentativas.

## Estrutura do projeto

```
desafio-1-assistente-dados/
├── pyproject.toml
├── README.md
├── .env.example
├── .gitignore
├── data/
│   └── clientes_completo.db
└── src/
    ├── __init__.py
    ├── agent/
    │   ├── __init__.py
    │   ├── graph.py          # LangGraph state machine (arquivo central)
    │   ├── state.py          # AgentState TypedDict
    │   ├── tools.py          # Wrappers de schema e SQL
    │   └── prompts.py        # System prompts para o LLM
    ├── db/
    │   ├── __init__.py
    │   └── connection.py     # Conexao SQLite read-only + introspeccao
    ├── viz/
    │   ├── __init__.py
    │   └── chart_picker.py   # Selecao heuristica de grafico + renderizacao
    └── app.py                # Frontend Streamlit
```
