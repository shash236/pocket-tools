from dataclasses import dataclass


@dataclass(frozen=True)
class Owner:
    name: str


def require_owner() -> Owner:
    """FastAPI dependency for routes that need the logged-in owner.

    TODO: check the session issued by core.admin.auth. Allows everyone for now.
    """
    return Owner(name="owner")
