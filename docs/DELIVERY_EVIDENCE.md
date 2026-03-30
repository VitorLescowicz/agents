# Delivery Evidence

## Repositorio

- GitHub: `VitorLescowicz/agents`
- branch principal: `main`

## Evidencias tecnicas

- os anexos originais foram preservados em `assets/`
- o setup automatizado e feito por `scripts/materialize_assets.py`
- a CI valida unit tests, smoke tests e integracao Gemini
- o desafio 1 passou a expor plano, trace e queries executadas
- o desafio 2 processa o dataset escaneado com OCR fallback

## Ultima validacao remota conhecida

- workflow `CI`
- run `#10`
- conclusao: `success`
- URL: `https://github.com/VitorLescowicz/agents/actions/runs/23758490456`

## Itens de destaque para entrevista

- por que o desafio 2 exigiu OCR de verdade
- por que o desafio 1 ganhou planejamento multi-etapas
- como a CI foi usada para detectar quota, modelo obsoleto e regressao de fluxo
- quais seriam os proximos passos para escalar custo, latencia e qualidade
