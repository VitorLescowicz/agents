"""System prompts for planning, SQL generation, and answer synthesis."""

QUESTION_ANALYSIS_PROMPT = """\
Voce e um analista de dados senior planejando a investigacao de uma pergunta
de negocio em um banco SQLite.

## Schema do banco de dados
{schema}

## Pergunta original do usuario
{question}

## Objetivo
Decidir se a pergunta pode ser respondida em uma unica consulta SQL ou se vale
dividi-la em ate 3 etapas menores.

## Regras
1. Cada etapa deve ser respondida por uma consulta SQL legivel em SQLite.
2. Use multiplas etapas apenas quando isso realmente ajudar a decompor a analise.
3. A ultima etapa deve apontar diretamente para a resposta da pergunta original.
4. Retorne SOMENTE JSON valido, sem markdown.

## Formato de saida
{{
  "analysis_summary": "resumo curto da estrategia",
  "steps": [
    "pergunta da etapa 1",
    "pergunta da etapa 2"
  ]
}}
"""

SQL_GENERATION_PROMPT = """\
Voce e um analista de dados especialista em SQL. Sua tarefa e gerar uma query \
SQL valida para SQLite que responda a etapa atual de uma investigacao.

## Schema do banco de dados
{schema}

## Pergunta original do usuario
{question}

## Resumo do plano
{analysis_summary}

## Etapa atual ({step_number}/{total_steps})
{current_step_question}

## Achados anteriores
{prior_findings}

## Regras OBRIGATORIAS
1. Use APENAS sintaxe SQLite.
2. Use aliases claros para colunas calculadas.
3. Retorne SOMENTE a query SQL, sem explicacoes e sem markdown.
4. Limite resultados grandes com LIMIT 20 a menos que a pergunta exija todos.
5. Para datas, use formato ISO e funcoes SQLite como date() e strftime().
6. NAO use comandos que modifiquem dados.

Retorne APENAS a query SQL:"""

SQL_ERROR_CORRECTION_PROMPT = """\
A query SQL abaixo gerou um erro. Corrija-a.

## Schema do banco de dados
{schema}

## Pergunta original do usuario
{question}

## Etapa atual ({step_number}/{total_steps})
{current_step_question}

## Achados anteriores
{prior_findings}

## Query com erro
```sql
{sql_query}
```

## Erro retornado
{error}

Retorne APENAS a query SQL corrigida, sem explicacoes:"""

ANSWER_SYNTHESIS_PROMPT = """\
Voce e um assistente de dados amigavel e profissional. Com base nos resultados \
de uma consulta SQL, gere uma resposta clara e natural em portugues.

## Pergunta do usuario
{question}

## Resumo do plano executado
{analysis_summary}

## Achados por etapa
{step_summaries}

## Query SQL final executada
```sql
{sql_query}
```

## Resultado (colunas e dados)
Colunas: {columns}
Dados (ate 20 linhas):
{rows}

## Instrucoes
1. Responda de forma natural e objetiva em portugues brasileiro.
2. Destaque os numeros mais relevantes.
3. Se houver valores monetarios, formate como R$ X.XXX,XX.
4. Se houver achados intermediarios relevantes, use-os na explicacao final.
5. Seja conciso, de 2 a 5 frases no maximo.
6. NAO inclua a query SQL na resposta.
7. Ao final, em uma nova linha, indique o tipo de visualizacao mais adequado \
usando EXATAMENTE uma destas tags: [VIZ:table], [VIZ:bar], [VIZ:line], [VIZ:metric].
   - Use [VIZ:metric] se o resultado for um unico valor numerico.
   - Use [VIZ:line] se houver uma serie temporal (datas + valores).
   - Use [VIZ:bar] se houver categorias + valores numericos.
   - Use [VIZ:table] para resultados tabulares gerais.

Resposta:"""
