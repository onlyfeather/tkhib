import os
from dataclasses import dataclass
from typing import Any

from nonebot import get_driver


@dataclass(frozen=True)
class AIConfig:
    api_key: str
    base_url: str
    model: str


def load_ai_config() -> AIConfig:
    nonebot_config: Any = get_driver().config
    api_key = (
        os.getenv("TKHIB_AI_API_KEY")
        or getattr(nonebot_config, "tkhib_ai_api_key", None)
        or os.getenv("CHAT_API_KEY")
        or getattr(nonebot_config, "chat_api_key", None)
    )
    base_url = (
        os.getenv("TKHIB_AI_BASE_URL")
        or getattr(nonebot_config, "tkhib_ai_base_url", None)
        or os.getenv("CHAT_BASE_URL")
        or getattr(nonebot_config, "chat_base_url", None)
    )
    model = (
        os.getenv("TKHIB_AI_MODEL")
        or getattr(nonebot_config, "tkhib_ai_model", None)
        or os.getenv("CHAT_MODEL")
        or getattr(nonebot_config, "chat_model", None)
    )

    missing = [
        name
        for name, value in {
            "TKHIB_AI_API_KEY": api_key,
            "TKHIB_AI_BASE_URL": base_url,
            "TKHIB_AI_MODEL": model,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing AI config: {', '.join(missing)}")

    return AIConfig(
        api_key=api_key,
        base_url=base_url.rstrip("/"),
        model=model,
    )


ai_config = load_ai_config()
