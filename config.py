from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    BOT_TOKEN: str
    BOT_USERNAME: str = "PassKnightBot"
    ADMIN_IDS: List[int] = [918330630]
    TRIBUTE_USERNAME: str = "tribute"
    YOOMONEY_WALLET: str = ""
    AGREEMENT_URL: str = ""
    PRIVACY_URL: str = ""

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, (int, float)):
            return [int(v)]
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
