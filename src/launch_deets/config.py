"""Local configuration loading; secret values are never printed."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_local_env(override: bool = False) -> None:
    """Load local credentials without requiring secrets inside the repository."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    # Use a local ignored .env or an explicitly configured private file.
    explicit = os.getenv("LAUNCH_DEETS_ENV_FILE")
    path = Path(explicit).expanduser() if explicit else ROOT / ".env"
    load_dotenv(path, override=override)


@dataclass(frozen=True)
class Settings:
    nebius_api_key: str | None
    nebius_base_url: str
    nebius_model: str | None
    nebius_embedding_model: str | None
    nebius_embedding_dimensions: int | None
    pinecone_api_key: str | None
    pinecone_index_name: str | None
    pinecone_namespace: str
    neo4j_uri: str | None
    neo4j_username: str | None
    neo4j_password: str | None
    langsmith_api_key: str | None
    langsmith_project: str
    typesafe_api_key: str | None
    typesafe_noul_threshold: float

    @classmethod
    def from_env(cls) -> "Settings":
        load_local_env()
        dims = os.getenv("NEBIUS_EMBEDDING_DIMENSIONS")
        return cls(
            nebius_api_key=os.getenv("NEBIUS_API_KEY"),
            nebius_base_url=os.getenv("NEBIUS_BASE_URL", "https://api.studio.nebius.com/v1"),
            nebius_model=os.getenv("NEBIUS_MODEL"),
            nebius_embedding_model=os.getenv("NEBIUS_EMBEDDING_MODEL"),
            nebius_embedding_dimensions=int(dims) if dims else None,
            pinecone_api_key=os.getenv("PINECONE_API_KEY"),
            pinecone_index_name=os.getenv("PINECONE_INDEX_NAME"),
            pinecone_namespace=os.getenv("PINECONE_NAMESPACE", "launch-deets-synthetic-v1"),
            neo4j_uri=os.getenv("NEO4J_URI"),
            neo4j_username=os.getenv("NEO4J_USERNAME"),
            neo4j_password=os.getenv("NEO4J_PASSWORD"),
            langsmith_api_key=os.getenv("LANGSMITH_API_KEY"),
            langsmith_project=os.getenv("LANGSMITH_PROJECT", "launch-deets"),
            typesafe_api_key=os.getenv("TYPESAFE_API_KEY"),
            typesafe_noul_threshold=float(os.getenv("TYPESAFE_NOUL_THRESHOLD", "0.5")),
        )

    def missing_for(self, *fields: str) -> list[str]:
        return [name.upper() for name in fields if not getattr(self, name)]


def configure_langsmith(settings: Settings) -> bool:
    """Enable LangSmith environment tracing if configured; report boolean only."""
    if not settings.langsmith_api_key:
        return False
    os.environ.setdefault("LANGSMITH_API_KEY", settings.langsmith_api_key)
    os.environ.setdefault("LANGSMITH_PROJECT", settings.langsmith_project)
    os.environ.setdefault("LANGSMITH_TRACING", "true")
    return True

