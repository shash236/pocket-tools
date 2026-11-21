from functools import lru_cache
from pathlib import Path
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="POCKET_", env_file=".env", extra="ignore")

    # The user's project: the folder holding modules/.
    project_dir: Path = Field(default_factory=Path.cwd)
    # Relative paths resolve against project_dir.
    data_dir: Path = Path("data")
    log_level: str = "INFO"

    @model_validator(mode="after")
    def _resolve_paths(self) -> Self:
        self.project_dir = self.project_dir.resolve()
        self.data_dir = (self.project_dir / self.data_dir).resolve()
        return self

    @property
    def modules_dir(self) -> Path:
        return self.project_dir / "modules"


@lru_cache
def get_settings() -> Settings:
    return Settings()
