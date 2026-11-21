import os


def get_secret(module_id: str, name: str) -> str | None:
    """Return a secret the module declared in its manifest.

    TODO: read from the encrypted vault managed by core.admin.secrets.
    For now: env var POCKET_SECRET_<MODULE>_<NAME>.
    """
    return os.environ.get(f"POCKET_SECRET_{module_id.upper()}_{name.upper()}")
