import math
import time
from collections.abc import Callable
from typing import TypeVar

from google.genai import errors as genai_errors
from google.genai import types

from .clientes import gemini
from .config import get_ia_settings

T = TypeVar("T")
_LOTE = 100  # limite de textos por requisição de embedding
_CODIGOS_RETENTAVEIS = {429, 500, 502, 503, 504}


def _com_retry(fn: Callable[[], T], tentativas: int = 4) -> T:
    for i in range(tentativas):
        try:
            return fn()
        except genai_errors.APIError as e:
            if e.code in _CODIGOS_RETENTAVEIS and i < tentativas - 1:
                time.sleep(2**i)
                continue
            raise
    raise RuntimeError("inalcançável")


def normalizar(vetor: list[float]) -> list[float]:
    """Com dimensão menor que 3072, o Gemini não devolve o vetor normalizado: normalizamos aqui."""
    norma = math.sqrt(sum(x * x for x in vetor))
    return [x / norma for x in vetor] if norma else vetor


def _embed(textos: list[str], task_type: str) -> list[list[float]]:
    cfg = get_ia_settings()
    resultado: list[list[float]] = []
    for i in range(0, len(textos), _LOTE):
        lote = textos[i : i + _LOTE]
        resp = _com_retry(
            lambda lote=lote: gemini().models.embed_content(
                model=cfg.gemini_embedding_model,
                contents=lote,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=cfg.embedding_dim,
                ),
            )
        )
        resultado.extend(normalizar(list(e.values)) for e in resp.embeddings)
    return resultado


def embed_documentos(textos: list[str]) -> list[list[float]]:
    return _embed(textos, "RETRIEVAL_DOCUMENT")


def embed_consulta(texto: str) -> list[float]:
    return _embed([texto], "RETRIEVAL_QUERY")[0]


def para_pgvector(vetor: list[float]) -> str:
    """Formato texto aceito pelo pgvector: '[0.1,0.2,...]'."""
    return "[" + ",".join(f"{x:.8f}" for x in vetor) + "]"
