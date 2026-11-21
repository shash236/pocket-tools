# Pocket Tools

Your own pocket-sized set of personal apps. Describe an app to your coding agent, it writes a
module, and it runs: locally, on your own server, or (later) hosted for you.

This repo is **`pocket-tools`**: the library that hosts modules. You don't fork or edit it;
your project depends on it.

> **Pre-alpha.** Owner login and the secrets vault are not built yet: every route is open.
> Run it only on your own machine; don't expose it to the internet.

## Start a project

```
uvx --from pocket-tools pocket init my-apps
cd my-apps
uv sync
uv run pocket new expenses
uv run pocket dev                              # http://127.0.0.1:8000
```

Your project contains only `pyproject.toml`, `AGENTS.md` (the guide your agent follows) and
`modules/`. Each module has its own API, UI, SQLite database and docs.

## Developing core

```
uv sync
uv run ruff check && uv run ruff format --check && uv run pyright && uv run pytest

cd examples/notes        # a real project using this checkout
uv run pocket dev
```

Start a project against a local checkout:
`uv run pocket init ../my-apps --core-path ../personal-apps`

See `docs/maintainers.md` for decisions, status and open questions.
