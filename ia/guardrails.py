import re
import unicodedata

MAX_PERGUNTA = 1000
MAX_TURNOS_HISTORICO = 8

_CRISE = (
    "me matar", "quero morrer", "quero me matar", "suicid", "tirar minha vida", "tirar a minha vida",
    "acabar com minha vida", "acabar com a minha vida", "nao quero mais viver", "automutil",
    "me machucar", "me cortar", "vou me matar", "melhor sem mim",
)
_SAUDACOES = {
    "oi", "ola", "bom dia", "boa tarde", "boa noite", "e ai", "oi tudo bem", "ola tudo bem",
    "tudo bem", "opa", "hello", "hi",
}


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]+", " ", sem_acento.lower()).strip()


def validar_pergunta(pergunta: str) -> str:
    pergunta = (pergunta or "").strip()
    if not pergunta:
        raise ValueError("Pergunta vazia.")
    if len(pergunta) > MAX_PERGUNTA:
        raise ValueError(f"Pergunta muito longa (máx. {MAX_PERGUNTA} caracteres).")
    return pergunta


def detectar_crise(pergunta: str) -> bool:
    texto = _normalizar(pergunta)
    return any(termo in texto for termo in _CRISE)


def eh_saudacao(pergunta: str) -> bool:
    return re.sub(r"\s+", " ", _normalizar(pergunta)) in _SAUDACOES


def higienizar_para_prompt(texto: str) -> str:
    """Impede que o usuário feche/abra as tags estruturais do prompt."""
    return re.sub(r"</?\s*(contexto|pergunta)\s*>", "", texto, flags=re.IGNORECASE)
