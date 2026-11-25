from functools import lru_cache

from google import genai
from supabase import Client, create_client

from .config import get_ia_settings


@lru_cache
def gemini() -> genai.Client:
    return genai.Client(api_key=get_ia_settings().gemini_api_key.get_secret_value())


@lru_cache
def supabase_admin() -> Client:
    cfg = get_ia_settings()
    return create_client(cfg.supabase_url, cfg.supabase_service_role_key.get_secret_value())
