from pydantic import BaseModel


class CatConfig(BaseModel):
    channel_name: str
    cooldown_seconds: int = 10
    error_messages: list[str] = ["404: Cat not found. Have you checked inside your closet?"]
