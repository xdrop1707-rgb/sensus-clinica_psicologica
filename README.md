# Sensus IA (Gemini + Supabase pgvector)

Assistente RAG que só responde sobre o Sensus.

## Como funciona
1. Pergunta validada (tamanho, tags do prompt higienizadas).
2. Detecção de crise (CVV 188 / SAMU 192) e saudação, sem LLM.
3. Embedding da pergunta (Gemini) e busca semântica no Supabase (`buscar_conhecimento`).
4. Nenhum trecho acima do limiar: recusa fixa, sem chamar o LLM.
5. Com trechos: Gemini responde só com base neles, seguindo o system prompt.

## Instalação
1. Supabase, SQL Editor: rode `sql/001_ia_conhecimento.sql`.
2. `pip install -r requirements-ia.txt`
3. Copie as variáveis de `.env.ia.example` para o seu `.env` (pegue a chave em https://aistudio.google.com/apikey).
4. Coloque o conteúdo real do Sensus em `dados/conhecimento/` (.md, .txt ou .pdf).
5. `python -m ia.ingestao`
6. Teste: `python -m ia.cli --debug` e ajuste `RAG_MIN_SIMILARITY`.

## Integração na API (main.py)
```python
from ia.router import criar_router
from app.suas_dependencias import obter_usuario_atual  # a dependência de auth que você já tem

app.include_router(criar_router(obter_usuario_atual))
```
Endpoint: `POST /ia/chat` com `{"pergunta": "...", "historico": [{"papel": "user|model", "texto": "..."}]}`.

## Testes
`pytest tests` (usa mocks, não chama Gemini nem Supabase).
