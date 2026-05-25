from pydantic import BaseModel


class DogConfig(BaseModel):
    error_messages: list[str] = ["404: Dog not found. Have you checked under the couch? 🛋️"]
