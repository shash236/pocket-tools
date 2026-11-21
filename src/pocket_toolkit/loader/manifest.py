from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class ManifestError(Exception):
    pass


class SecretDecl(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(pattern=r"^[A-Z][A-Z0-9_]*$")
    description: str = ""
    optional: bool = False


class Manifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    name: str
    version: str = "0.1.0"
    icon: str = "box"
    description: str = ""
    secrets: list[SecretDecl] = []
    depends_on: list[str] = []


def read_manifest(module_dir: Path) -> Manifest:
    path = module_dir / "manifest.yaml"
    if not path.is_file():
        raise ManifestError(f"{module_dir.name}: missing manifest.yaml")
    try:
        manifest = Manifest.model_validate(yaml.safe_load(path.read_text()))
    except (yaml.YAMLError, ValidationError) as e:
        raise ManifestError(f"{module_dir.name}: invalid manifest.yaml\n{e}") from e
    if manifest.id != module_dir.name:
        raise ManifestError(
            f"{module_dir.name}: manifest id '{manifest.id}' must match the folder name"
        )
    return manifest
