import os
from pathlib import Path

from langchain_ollama import ChatOllama

DEFAULT_OLLAMA_MODEL = "gpt-oss:20b"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_VALIDATE_MODEL_ON_INIT = False


def _load_local_env() -> None:
    """Load a simple .env file from the project directory if present."""
    env_path = Path(__file__).parents[1] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_ollama_settings() -> tuple[str, str]:
    _load_local_env()
    model_name = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
    base_url = os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL)
    return model_name, base_url


def _should_validate_model_on_init() -> bool:
    _load_local_env()
    raw_value = os.getenv("OLLAMA_VALIDATE_MODEL_ON_INIT", "").strip().lower()
    if not raw_value:
        return DEFAULT_VALIDATE_MODEL_ON_INIT

    return raw_value in {"1", "true", "yes", "on"}


def format_ollama_runtime_error(base_url: str, model_name: str) -> str:
    message = (
        "Failed to call the Ollama chat model. Make sure Ollama is "
        f"reachable at {base_url} and the model '{model_name}' is available locally."
    )
    if "localhost" in base_url or "127.0.0.1" in base_url:
        message += (
            " If LangGraph is running in a container, use "
            "'http://host.docker.internal:11434' instead of 'http://localhost:11434'."
        )
    return message


def build_chat_model() -> ChatOllama:
    model_name, base_url = get_ollama_settings()
    validate_model_on_init = _should_validate_model_on_init()

    try:
        return ChatOllama(
            model=model_name,
            base_url=base_url,
            temperature=0,
            validate_model_on_init=validate_model_on_init,
        )
    except Exception as exc:
        raise RuntimeError(
            format_ollama_runtime_error(base_url, model_name)
        ) from exc
