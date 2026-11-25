import logging
from dataclasses import dataclass, field
from typing import Literal

from google.genai import types

from .clientes import gemini, supabase_admin
from .config import get_ia_settings
from .embeddings import embed_consulta, para_pgvector
from .guardrails import (
    MAX_TURNOS_HISTORICO,
    detectar_crise,
    eh_saudacao,
    higienizar_para_prompt,
    validar_pergunta,
)
from .prompts import (
    MENSAGEM_CRISE,
    MENSAGEM_ERRO_GERACAO,
    MENSAGEM_FORA_ESCOPO,
    MENSAGEM_SAUDACAO,
    SYSTEM_INSTRUCTION,
)

logger = logging.getLogger("sensus.ia")


class ErroServicoIA(Exception):
    """Falha de infraestrutura (Gemini/Supabase). O router converte em HTTP 503."""


@dataclass(frozen=True)
class Turno:
    papel: Literal["user", "model"]
    texto: str


@dataclass(frozen=True)
class RespostaIA:
    texto: str
    dentro_do_escopo: bool
    motivo: str  # ok | saudacao | crise | sem_contexto | resposta_vazia
    fontes: list[str] = field(default_factory=list)
    similaridade_max: float | None = None


def _sanitizar_historico(historico: list[Turno] | None) -> list[Turno]:
    turnos = [t for t in (historico or []) if t.texto.strip()][-MAX_TURNOS_HISTORICO:]
    while turnos and turnos[0].papel != "user":  # Gemini exige começar por "user"
        turnos.pop(0)
    return turnos


def _buscar_contexto(consulta: str) -> list[dict]:
    cfg = get_ia_settings()
    vetor = embed_consulta(consulta)
    resp = supabase_admin().rpc(
        "buscar_conhecimento",
        {
            "query_embedding": para_pgvector(vetor),
            "match_count": cfg.rag_top_k,
            "match_threshold": cfg.rag_min_similarity,
        },
    ).execute()
    return resp.data or []


def _montar_prompt(pergunta: str, trechos: list[dict]) -> str:
    blocos = "\n\n".join(f"[{i}] (fonte: {t['fonte']})\n{t['conteudo']}" for i, t in enumerate(trechos, 1))
    return f"<contexto>\n{blocos}\n</contexto>\n\n<pergunta>\n{higienizar_para_prompt(pergunta)}\n</pergunta>"


def responder(pergunta: str, historico: list[Turno] | None = None) -> RespostaIA:
    """Pipeline: validação -> crise -> saudação -> retrieval (porteiro de escopo) -> geração."""
    cfg = get_ia_settings()
    pergunta = validar_pergunta(pergunta)  # ValueError em caso de entrada inválida
    turnos = _sanitizar_historico(historico)

    # 1) Camadas determinísticas: não dependem do LLM e não podem ser "convencidas" por prompt injection
    if detectar_crise(pergunta):
        return RespostaIA(MENSAGEM_CRISE, True, "crise")
    if eh_saudacao(pergunta):
        return RespostaIA(MENSAGEM_SAUDACAO, True, "saudacao")

    # 2) Retrieval. Perguntas de seguimento ("e como faço isso?") herdam o contexto da pergunta anterior
    ultima_do_usuario = next((t.texto for t in reversed(turnos) if t.papel == "user"), "")
    consulta = f"{ultima_do_usuario}\n{pergunta}".strip()
    try:
        trechos = _buscar_contexto(consulta)
    except Exception as e:
        logger.exception("Falha no retrieval")
        raise ErroServicoIA("retrieval") from e

    # 3) Porteiro de escopo: nada relevante na base do Sensus = recusa fixa, sem chamar o LLM
    if not trechos:
        logger.info("fora_do_escopo (sem trechos acima de %.2f)", cfg.rag_min_similarity)
        return RespostaIA(MENSAGEM_FORA_ESCOPO, False, "sem_contexto")

    # 4) Geração. O histórico guarda só pergunta/resposta "limpas"; o contexto vai apenas no turno atual
    contents = [types.Content(role=t.papel, parts=[types.Part(text=t.texto)]) for t in turnos]
    contents.append(types.Content(role="user", parts=[types.Part(text=_montar_prompt(pergunta, trechos))]))

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=cfg.ia_temperature,
        max_output_tokens=cfg.ia_max_output_tokens,
    )
    if cfg.gemini_thinking_budget is not None:
        config.thinking_config = types.ThinkingConfig(thinking_budget=cfg.gemini_thinking_budget)

    try:
        resp = gemini().models.generate_content(model=cfg.gemini_chat_model, contents=contents, config=config)
    except Exception as e:
        logger.exception("Falha na geração")
        raise ErroServicoIA("geracao") from e

    texto = (resp.text or "").strip()
    similaridade = max(float(t["similaridade"]) for t in trechos)
    if not texto:
        return RespostaIA(MENSAGEM_ERRO_GERACAO, True, "resposta_vazia", similaridade_max=similaridade)

    fontes = sorted({t["fonte"] for t in trechos})
    # Não logamos o conteúdo da pergunta: pode conter dado sensível de saúde (LGPD)
    logger.info("ok trechos=%d sim_max=%.3f", len(trechos), similaridade)
    return RespostaIA(texto, True, "ok", fontes, similaridade)
