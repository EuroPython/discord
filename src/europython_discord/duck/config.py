from pydantic import BaseModel


class DuckConfig(BaseModel):
    channel_name: str
    cooldown_seconds: int = 10
    error_messages: list[str] = ["404: Duck not found. Have you checked the pond? 🦆"]
