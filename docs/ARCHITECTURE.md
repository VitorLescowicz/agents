# Architecture Notes

Este documento resume a arquitetura final do repositorio e serve como apoio para entrevista tecnica.

## Visao Geral

```text
assets/ -> scripts/materialize_assets.py
       -> desafio-1-assistente-dados/
       -> desafio-2-pipeline-documentos/

GitHub Actions / Codespaces
  -> setup de ambiente
  -> materializacao dos anexos
  -> unit tests
  -> smoke tests
  -> integracao Gemini
```

## Desafio 1

Objetivo: responder perguntas de negocio em linguagem natural sobre SQLite com transparência do processo.

Fluxo:

```text
discover_schema
  -> analyze_question
  -> plan_query
  -> execute_sql
  -> handle_error (quando a SQL falha)
  -> advance_plan
  -> synthesize_answer
```

Decisoes principais:

- introspeccao dinamica do schema para evitar SQL hardcoded
- planejamento explicito em ate 3 etapas para perguntas compostas
- retry semantico de SQL quando a execucao falha
- trilha de execucao exposta na UI, incluindo plano, queries tentadas e achados
- visualizacao hibrida: preferencia do LLM com fallback heuristico local

Trade-offs:

- o planejamento multi-etapas melhora explicabilidade, mas aumenta consumo de tokens
- manter SQLite read-only reduz risco operacional, em troca de limitar tipos de exploracao
- visualizacao baseada em heuristica e tag e simples de manter, mas nao cobre todos os casos analiticos possiveis

## Desafio 2

Objetivo: processar PDFs digitalizados e produzir dados estruturados confiaveis.

Fluxo:

```text
data/raw PDFs
  -> ingestao (PyMuPDF)
  -> OCR fallback (Tesseract)
  -> classificacao (Gemini)
  -> roteamento por tipo
  -> extracao estruturada (Gemini + Pydantic)
  -> persistencia (JSON + CSV + processing_log)
```

Decisoes principais:

- OCR obrigatorio porque o dataset entregue e predominantemente escaneado
- separacao entre classificacao e extracao para reduzir acoplamento e simplificar manutencao
- schemas Pydantic para impor formato estrito e orientar retries
- persistencia em formatos simples para facilitar auditoria e integracao futura com ERP
- backoff exponencial para falhas transitórias do LLM

Trade-offs:

- processamento sequencial privilegia previsibilidade e robustez sobre throughput maximo
- usar LLM em classificacao e extracao aumenta flexibilidade, mas exige controle de custo e quota

## Operacao e Qualidade

- unit tests cobrem parsing e utilitarios criticos
- smoke tests cobrem schema/SQL no desafio 1 e OCR no desafio 2
- integracao com Gemini valida o caminho completo em CI quando `GOOGLE_API_KEY` esta presente
- Codespaces e workflow de CI mantem ambiente reproduzivel

## O Que Excede o Pedido Original

- implementacao funcional dos dois desafios, apesar do enunciado pedir apenas um completo
- OCR real no desafio 2 para o dataset fornecido
- planejamento multi-etapas e transparencia detalhada no desafio 1
- CI com validacao automatica de smoke, unit e integracao
- repositorio preparado para Codespaces
