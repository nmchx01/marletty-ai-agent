import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

# No sobrescribe variables inyectadas por systemd/OCI.
load_dotenv(ENV_PATH, override=False)


@dataclass(frozen=True)
class Settings:
    """Configuración central de la aplicación."""

    base_dir: Path = BASE_DIR
    frontend_dir: Path = BASE_DIR / "frontend"
    docs_dir: Path = BASE_DIR / "backend" / "docs"
    vector_store_dir: Path = BASE_DIR / "backend" / "vector_store"
    env_path: Path = ENV_PATH
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    google_embedding_model: str = os.getenv(
        "GOOGLE_EMBEDDING_MODEL", "gemini-embedding-001"
    )
    google_embedding_dimension: int | None = (
        int(os.environ["GOOGLE_EMBEDDING_DIMENSION"])
        if os.getenv("GOOGLE_EMBEDDING_DIMENSION")
        else None
    )
    allowed_origins_raw: str = os.getenv("ALLOWED_ORIGINS", "*")
    supabase_url: str = os.getenv("SUPABASE_URL", "").rstrip("/")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")

    @property
    def allowed_origins(self) -> list[str]:
        if self.allowed_origins_raw.strip() == "*":
            return ["*"]
        return [
            origin.strip()
            for origin in self.allowed_origins_raw.split(",")
            if origin.strip()
        ]

    def require_google_api_key(self) -> None:
        if not self.google_api_key:
            raise RuntimeError("No se encontró GOOGLE_API_KEY en el entorno.")

    def require_groq_api_key(self) -> None:
        if not self.groq_api_key:
            raise RuntimeError("No se encontró GROQ_API_KEY en el entorno.")

    @property
    def supabase_enabled(self) -> bool:
        return bool(self.supabase_url and self.supabase_anon_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
