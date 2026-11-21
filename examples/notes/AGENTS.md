# Agent guide

This project holds the owner's personal mini apps ("modules"), run by **Pocket Tools**
(`pocket-tools`, an installed Python package). You are helping the owner add or change modules.

## What you may change

- **`modules/`** and **`tests/`**: yours to edit.
- **Never edit the installed `pocket_tools` package**, and don't vendor or monkeypatch it. Projects
  are deployed onto a stock `pocket-tools`, so changes to it would not exist in production.
  If a task truly needs something core lacks, stop and tell the owner what is missing.
- Leave `pyproject.toml` alone unless the owner asks. Don't add dependencies: deployed projects
  only get what `pocket-tools` provides.

## Layout

```
modules/<id>/    one folder per module
tests/           tests: tests/test_<id>.py
data/            runtime SQLite files (gitignored, never commit)
```

## A module

```
modules/<id>/
  manifest.yaml        id (= folder name), name, version, icon, description, secrets, depends_on
  __init__.py
  api.py               `router = APIRouter()`: thin HTTP layer, calls services
  services.py          business logic; owns all SQL
  models.py            pydantic models
  interface.py         public functions/models other modules may import
  migrations/NNN_*.sql numbered SQL, applied once in order at startup
  ui/index.html        no-build SPA (plain HTML/JS; a CDN script like Alpine or htmx is fine)
  README.md            what it does, its API, its interface, its tables
```

Served at: UI `/m/<id>/`, API `/m/<id>/api/...`.

## Creating a module

1. `uv run pocket new <id>` (id: lowercase, `a-z0-9_`, starts with a letter).
2. Fill in `manifest.yaml`; rename the template's `items` entity to your own in every file.
3. Write the migration, services, API and UI. Update the module's README.md.
4. Add `tests/test_<id>.py` using the `client` fixture, and run the checks below.

## Rules for module code

- **Imports:** only `pocket_tools.sdk.*`, your own module (relative imports), other modules'
  `interface` (e.g. `from modules.notes.interface import list_notes`), the standard library,
  and packages `pocket-tools` already installs (fastapi, pydantic, httpx, yaml).
  Never import other parts of `pocket_tools`, or another module's services, models or database.
  `pocket check` enforces this.
- **Database:** `db = ModuleDB.for_module(__name__)` from `pocket_tools.sdk.db`. Each module has its
  own `data/<id>.db`. Always use `?` parameters, never string-formatted SQL.
- **Files:** keep all state in the module's database; don't write files anywhere else.
- **Migrations:** add a new numbered file for every change. Never edit or delete a migration
  that has been committed. Additive changes only (new tables, new columns); no `DROP` or renames.
- **Secrets:** declare them in `manifest.yaml` under `secrets`, read them with
  `pocket_tools.sdk.secrets.get_secret("<id>", "NAME")`. Never hardcode keys, never log them.
- **Auth:** API routers use `dependencies=[Depends(require_owner)]` from `pocket_tools.sdk.auth`.
- **UI:** call your API with relative paths (`fetch("api/items")`), never absolute ones.
  Use `textContent` for user data, not `innerHTML`.

## Checks (run all before saying you're done)

```
uv run pocket check
uv run ruff check --fix && uv run ruff format
uv run pyright
uv run pytest
```

Then `uv run pocket dev` and open `http://127.0.0.1:8000/m/<id>/` to confirm it loads.
