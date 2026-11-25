from collections.abc import Callable
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from .agente import ErroServicoIA, Turno, responder
from .guardrails import MAX_PERGUNTA, MAX_TURNOS_HISTORICO


class MensagemIn(BaseModel):
    papel: Literal["user", "model"]
    texto: str = Field(min_length=1, max_length=2000)


class ChatIn(BaseModel):
    pergunta: str = Field(min_length=1, max_length=MAX_PERGUNTA)
    historico: list[MensagemIn] = Field(default_factory=list, max_length=MAX_TURNOS_HISTORICO)


class ChatOut(BaseModel):
    resposta: str
    dentro_do_escopo: bool
    fontes: list[str]


def criar_router(dependencia_auth: Callable[..., Any]) -> APIRouter:
    """Recebe a dependência de autenticação que você JÁ tem (a que valida o JWT do Supabase)."""
    router = APIRouter(prefix="/ia", tags=["IA"], dependencies=[Depends(dependencia_auth)])

    # `def` (síncrono): o FastAPI executa em threadpool, então as chamadas bloqueantes não travam o event loop
    @router.post("/chat", response_model=ChatOut)
    def chat(body: ChatIn) -> ChatOut:
        try:
            r = responder(body.pergunta, [Turno(m.papel, m.texto) for m in body.historico])
        except ValueError as e:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e)) from e
        except ErroServicoIA as e:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Assistente indisponível no momento.") from e
        return ChatOut(resposta=r.texto, dentro_do_escopo=r.dentro_do_escopo, fontes=r.fontes)

    return router
