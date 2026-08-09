## global level config that manages everything

from dataclasses import dataclass


@dataclass(frozen=True)
class OllamaConfig:
    DEFAULT_HOST: str = "http://localhost:11434"
    DEFAULT_MODEL: str = "qwen2.5-coder:7b"


@dataclass(frozen=True)
class MessageConfig:
    MAX_ATTEMPTS: int = 4
    RETRY_BASE_DELAY: float = 0.5
