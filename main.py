from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ia.auth import obter_usuario_atual
from ia.config import get_ia_settings
from ia.router import criar_router

app = FastAPI(title="Sensus IA", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_ia_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(criar_router(obter_usuario_atual))


@app.get("/health", tags=["infra"])
def health() -> dict[str, str]:
    return {"status": "ok"}
