## global level config that manages everything 

from dataclasses import dataclass
from pydantic import HttpUrl

@dataclass(frozen=True)
class OllamaConfig:
    DEFAULT_HOST: HttpUrl = "http://localhost:11434"
    DEFAULT_MODEL: str = "qwen2.5-coder:7b"
    
@dataclass(frozen=True)
class MessageConfig:
    MAX_ATTEMPTS: int = 4 
    RETRY_BASE_DELAY: int = 0.5 