from fastapi.testclient import TestClient

import main
from ia import router as router_mod
from ia.agente import RespostaIA
from ia.auth import obter_usuario_atual


def test_chat_exige_token():
    c = TestClient(main.app)
    assert c.post("/ia/chat", json={"pergunta": "oi"}).status_code == 401


def test_chat_autenticado(monkeypatch):
    main.app.dependency_overrides[obter_usuario_atual] = lambda: object()
    monkeypatch.setattr(router_mod, "responder", lambda p, h: RespostaIA("ok!", True, "ok", ["faq.md"]))
    try:
        r = TestClient(main.app).post("/ia/chat", json={"pergunta": "como funciona?", "historico": []})
    finally:
        main.app.dependency_overrides.clear()
    assert r.status_code == 200 and r.json() == {"resposta": "ok!", "dentro_do_escopo": True, "fontes": ["faq.md"]}


def test_health():
    assert TestClient(main.app).get("/health").json() == {"status": "ok"}
