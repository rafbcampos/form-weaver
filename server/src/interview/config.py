from __future__ import annotations

import os


class Settings:
    def __init__(self) -> None:
        self.llm_model: str = os.environ.get("LLM_MODEL", "anthropic/claude-sonnet-4-5-20250929")
        self.cors_origins: list[str] = os.environ.get(
            "CORS_ORIGINS", "http://localhost:5173"
        ).split(",")
        self.host: str = os.environ.get("HOST", "0.0.0.0")  # noqa: S104
        self.port: int = int(os.environ.get("PORT", "8000"))

    @property
    def llm_provider(self) -> str:
        """Extract provider from model string (e.g. 'anthropic' from 'anthropic/claude-...')."""
        return self.llm_model.split("/")[0] if "/" in self.llm_model else "openai"

    def validate_api_key(self) -> None:
        """Validate that the required API key is set for the configured provider."""
        provider = self.llm_provider
        key_map: dict[str, str] = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
        }
        env_var = key_map.get(provider)
        if env_var and not os.environ.get(env_var):
            msg = (
                f"{env_var} environment variable is required "
                f"for provider '{provider}'. "
                f"Set it before starting the server, or change "
                f"LLM_MODEL to use a different provider.\n"
                f"Supported: anthropic (default), openai\n"
                f"Examples:\n"
                f"  LLM_MODEL=anthropic/claude-sonnet-4-5-20250929\n"
                f"  LLM_MODEL=openai/gpt-4o"
            )
            raise RuntimeError(msg)


settings = Settings()
