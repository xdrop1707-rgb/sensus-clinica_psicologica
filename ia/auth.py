from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .clientes import supabase_admin

_bearer = HTTPBearer(auto_error=False)


def obter_usuario_atual(cred: HTTPAuthorizationCredentials | None = Depends(_bearer)):
    """Valida o token (access_token do login do Supabase) perguntando ao próprio Supabase Auth."""
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token ausente.")
    try:
        resp = supabase_admin().auth.get_user(cred.credentials)
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido ou expirado.") from None
    if resp is None or resp.user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido ou expirado.")
    return resp.user
