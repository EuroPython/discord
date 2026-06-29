from pydantic import BaseModel


class FoxConfig(BaseModel):
    channel_name: str
    cooldown_seconds: int = 10
    error_messages: list[str] = ["404: Fox not found. Have you checked the den? 🦊"]
