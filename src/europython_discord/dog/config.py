from pydantic import BaseModel


class DogConfig(BaseModel):
    channel_name: str = "pet-appreciation"
    cooldown_seconds: int = 10
    error_messages: list[str] = ["404: Dog not found. Have you checked under the couch? 🛋️"]
