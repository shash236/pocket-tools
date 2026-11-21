# Personal AI Mini-App Platform: Architecture & Milestones

Oct 15, 2026 · @Shashwatik Sinha

## Summary

A self-hostable platform for AI mini apps: each user runs one or more **instances** (a FastAPI + SQLite server on a Mac, EC2 or a rented box), and a **PWA** links to those instances and shows their mini apps as a home-screen grid.

New apps are built by chatting with Claude or ChatGPT: **Add new** gives a scoped link (an MCP endpoint), the AI pushes code to **beta**, the owner tests and **approves**, and the app joins the grid. Secrets and env vars live in an encrypted vault on the instance; the AI never sees their values.

The MVP runs on a MacBook Air: instance + PWA + MCP endpoints + Claude-built mini apps.

## Core concepts

| Concept | What it is |
| --- | --- |
| Instance | One server running the host service. Hosts many mini apps. Runs on a Mac, EC2, or a box rented from us. |
| Mini app | A module: SPA + API + SQLite + icon + declared secrets + optional AI calls. Runs on exactly one instance. |
| PWA client | The app people install. Links to one or more instances, shows a combined grid, handles beta testing, approve, secrets and settings. |
| Build session | Created by **Add new** (or **Edit with AI**). A scoped, expiring MCP link the user hands to Claude or ChatGPT. Can only write one draft and push it to beta. |
| Beta | A per-app preview slot running the draft against a copy of the app's data. Only a human approve promotes it. |
| Secrets vault | Encrypted env vars on each instance, injected only into the apps that declare them. |
| Marketplace | Central catalog of signed app bundles (later stage). |

## Instance architecture

Each instance is one Docker image: a FastAPI modulith that starts every mini app as its own sandboxed process.

&#91;embedded content: instance architecture · 8 host modules, sandboxed apps\]

A PWA request enters through the edge, the host API checks the owner session, and the process manager proxies it to that app's process over a unix socket. Claude reaches only the MCP server, which can write a draft and start its beta.

## Mini app module format

A mini app is one folder with four required parts; the host runs it, so it ships no server, port or Dockerfile.

```
apps/expenses/
  manifest.yaml       # identity, permissions, env vars
  api.py              # FastAPI APIRouter
  web/                # no-build SPA (index.html, app.js)
  migrations/         # numbered SQL files, additive only
  README.md           # what it does; helps the AI
```

```yaml
id: expenses
name: Expenses
version: 0.3.0
icon: wallet
env:
  - { name: CURRENCY, default: INR }
  - { name: SPLITWISE_TOKEN, secret: true, optional: true }
db:
  share: read          # none | read | read-write: what others may do with my data
  reads: [core]        # data I need from other apps on this instance
network: [api.splitwise.com, openrouter.ai]
llm: { monthly_budget_usd: 5 }
```

```python
from fastapi import APIRouter
from host_sdk import ctx  # ctx.db, ctx.env, ctx.llm

router = APIRouter()


@router.get("/items")
def list_items():
    return ctx.db.query("SELECT * FROM items ORDER BY ts DESC")
```

- The SPA calls its API with relative paths (`fetch("api/items")`), so the same code runs in beta and prod.
- A module never holds secret values, file paths or DB paths: everything goes through `ctx`.
- `ctx.llm` calls the instance's LLM gateway; the app never sees the OpenRouter key.

## Data model

Every app gets its own SQLite file; sharing is a permission, not a shared database.

- **Storage:** `data/<app>.db` per app, plus a host-owned `core.db` (profile, tags, contacts). WAL mode and a `busy_timeout` on every file.
- **Sharing:** the manifest declares `share` and `reads`. At start the host opens the app's own file and `ATTACH`es each granted file, read-only unless its owner allows writes. App code queries `expenses.items` like a local table.
- **Owner override:** the PWA can revoke any grant, like phone app permissions.
- **Real enforcement:** the sandbox mounts only the app's own file read-write and granted files read-only. `ATTACH ... mode=ro` alone is not security, since app code could open files directly.
- **Beta:** copies only that app's file. Rollback stays per app.
- **Migrations:** run by the host on push-to-beta and on approve. Additive only (add tables or columns); drops and renames are rejected.
- **Limits:** cross-file transactions are not fully atomic, and sharing only works between apps on the same instance.

## Build and release flow

The AI can only ever reach beta; promoting to the grid is a human action in the PWA.

1. **Add new** in the PWA creates a build session: a draft app, an empty `beta/<app>` branch and a token scoped to that draft, expiring in hours. The PWA opens the share sheet with the link.
2. The user adds the link to Claude or ChatGPT and describes the app. The AI calls `get_conventions` to learn the module format.
3. The AI writes files with `write_files`, declares env vars with `declare_env`, then calls `push_to_beta`.
4. The host commits to `beta/<app>`, runs migrations on a copy of the app's DB, and starts a beta process. The AI reads errors through `get_beta_logs` (secrets scrubbed) and iterates.
5. The PWA notifies the user. They fill any requested secrets, test the beta URL, and review the code diff plus permission changes.
6. **Approve** merges `beta/<app>` into `main`, runs migrations on prod data, and restarts the prod process. The app appears as a tile.
7. **Rollback** reverts `main` to the previous version in one tap. **Reject** discards the beta.

**Edit with AI** on an existing tile runs the same flow, scoped to that app and its beta.

Build session tools: `get_conventions`, `list_files`, `write_files`, `declare_env`, `push_to_beta`, `get_beta_logs`. There is no approve, delete or secret-read tool.

## PWA client and multi-instance

The PWA hosts nothing: it pairs with instances and shows their apps.

- **Pairing:** the instance's web UI shows a QR code with its URL and a one-time code. The PWA exchanges it for a device token. Devices are revocable from instance settings.
- **Grid:** `GET /api/apps` on each paired instance builds one combined grid; each tile is tagged with its instance.
- **Screens:** app grid, beta test view with approve or reject and the permission diff, secrets entry, instance links and configuration, settings, and **Add new**.
- **Isolation:** each app is served on its own subdomain (`expenses.<instance-domain>`) through a wildcard cert, so apps cannot read each other's cookies or storage.
- **Multi-instance (detail parked):** one PWA links to several instances, and the user picks which instance each app runs on. Moving an app later = copy its folder and DB file, then re-enter its secrets.
- **Later:** an Expo/React Native shell for Face ID on approve and reliable push; Tauri for desktop.

## Security model

Treat every mini app's code as untrusted, including code the owner's own AI wrote, and wall it in with the OS sandbox.

| Threat | Defence |
| --- | --- |
| Strangers on the public URL | Owner passkey; every app route needs the owner session by default; MCP over OAuth with short-lived tokens; optional Cloudflare Access in front |
| Leaked build link | Scoped to one draft, expires in hours, revocable; can only write the draft and push to beta |
| Bad or prompt-injected app code | Unprivileged process per app in a container or bubblewrap/nsjail; read-only filesystem except its data folder; CPU and memory limits; pre-installed dependency allowlist |
| Data exfiltration | Network denied by default; egress proxy allows only manifest domains |
| Apps reading each other | Sandbox mounts only granted DB files, read-only; per-app subdomains in the PWA |
| Secret leaks | Encrypted at rest, master key in macOS Keychain or AWS KMS; injected only into apps that declare them; AI sees names only; logs scrubbed before `get_beta_logs`; separate beta and prod values |
| LLM cost abuse | Gateway holds the OpenRouter key; per-app model allowlist and monthly budget |
| Unreviewed changes | Human-only approve showing the code diff and permission changes |
| Supply chain | Signed marketplace bundles and host image updates; encrypted backups |

On a Mac, run the instance inside Docker (OrbStack) so the Linux sandbox tools work the same as on EC2.

## Deployment targets and tech stack

One Docker image runs everywhere; only the public-URL setup differs per target.

| Target | Runs as | Public URL | Notes |
| --- | --- | --- | --- |
| MacBook Air (MVP) | Docker via OrbStack | Cloudflare Tunnel | Must stay awake: plugged in, `caffeinate`, lid open or clamshell |
| Mac mini | Docker via OrbStack | Cloudflare Tunnel | Always-on home server |
| EC2 / any VPS | `docker compose up` or one-line install | Caddy with auto-TLS | Master key in AWS KMS |
| Rented from us | Same image on our infra | Our domain | Later stage: provisioning and billing |

| Layer | Choice |
| --- | --- |
| Host service | Python, FastAPI, uvicorn |
| App runtime | One uvicorn process per app version on a unix socket, in a container or bubblewrap sandbox |
| Data | SQLite per app + `core.db`, WAL mode; Litestream for backups (later) |
| Versioning | Bare git repo on the instance; `main` = prod, `beta/<app>` = drafts |
| Migrations guard | `sqlglot` to reject destructive SQL |
| Secrets | libsodium/age encryption; Keychain or KMS master key |
| MCP | Python MCP SDK over streamable HTTP, OAuth |
| LLM | OpenRouter through the host gateway |
| Edge | Caddy (wildcard cert, per-app subdomains) or cloudflared |
| Client | PWA (React + Vite); later Expo shell |
| Mini app UI | No-build SPA: plain HTML/JS, htmx or Alpine from a CDN |

## Repo layout

One monorepo for the platform; each user's mini apps live in a separate git repo on their own instance.

```
platform/
  host/                 # FastAPI modulith
    auth/               # owner passkey, device pairing, sessions
    registry/           # installed apps, manifests, versions
    runtime/            # process manager, sandbox, proxy
    gitops/             # bare repo, beta branches, approve, rollback
    storage/            # SQLite files, ATTACH grants, migrations guard
    secrets/            # vault, injection, log scrubbing
    llm/                # OpenRouter gateway, budgets
    mcp/                # build sessions and tools
    api/                # REST API for the PWA
  sdk/host_sdk/         # ctx.db, ctx.env, ctx.llm for mini apps
  pwa/                  # client app
  templates/mini-app/   # starter module + conventions doc for the AI
  examples/             # sample apps: notes, expenses, chat
  deploy/               # Dockerfile, compose, Caddyfile, install script
  docs/                 # architecture, ADRs
```

Module boundaries inside `host/` are enforced with import rules (for example `import-linter`), so the modulith can split later without a rewrite.

## Stages and milestones

Four stages, each closed by a gate you can demo; the MVP is done at Gate 2.

&#91;embedded content: roadmap · 4 stages, 12 milestones, 4 gates\]

Milestones run in order within a stage; Stage 4 milestones can go in any order.

### Stage 1 · Core runtime

**M0 Foundations.** Done when `docker compose up` serves the host on the MacBook Air.

- [ ] Monorepo with `host/`, `sdk/`, `pwa/`, `templates/`, `deploy/`
- [ ] FastAPI host skeleton: health endpoint, config, logging
- [ ] Dockerfile and compose, running under OrbStack
- [ ] CI: lint, type check, tests, module boundary rules

**M1 One app runs.** Done when a hand-written notes app works end to end and its data survives a restart.

- [ ] Manifest schema and validation
- [ ] Process manager: one uvicorn process per app on a unix socket
- [ ] Reverse proxy for `/apps/<name>/` and static SPA serving
- [ ] Per-app SQLite, migrations runner, `ctx.db` and `ctx.env`
- [ ] Sample notes app

**M2 Secrets + LLM.** Done when an app calls `ctx.llm` without ever seeing the OpenRouter key.

- [ ] Vault: encryption at rest, master key in Keychain or env
- [ ] Env injection per process from manifest declarations
- [ ] Owner secrets API
- [ ] LLM gateway: model allowlist, per-app budget, usage log
- [ ] Secret scrubbing in logs

**M3 Beta + approve.** Done when a change goes beta, approve, prod, and rollback restores the old version. **Gate 1.**

- [ ] Bare git repo per instance with `main` and `beta/<app>`
- [ ] Beta process on a copy of the app's DB
- [ ] Approve = merge + migrations + restart; rollback = revert
- [ ] Migration guard with `sqlglot`
- [ ] Read-only ATTACH grants from manifest `reads`

### Stage 2 · MVP demo

**M4 MCP builds.** Done when Claude, given a build link, creates a new mini app in beta.

- [ ] MCP server over streamable HTTP with OAuth
- [ ] Build sessions: scoped, expiring, revocable tokens
- [ ] Tools: `get_conventions`, `list_files`, `write_files`, `declare_env`, `push_to_beta`, `get_beta_logs`
- [ ] Conventions doc and starter template for the AI
- [ ] Cloudflare Tunnel setup

**M5 PWA client.** Done when, from a phone, you tap Add new, build with Claude, approve, and use the app. **Gate 2: MVP demo.**

- [ ] Owner passkey login, QR pairing, device tokens
- [ ] App grid and Add new with the share sheet
- [ ] Beta view: test, code diff, permission changes, approve or reject
- [ ] Secrets screen and settings
- [ ] Per-app subdomains with a wildcard cert
- [ ] Stretch: push notification when a beta is ready

### Stage 3 · Safe for others

**M6 Sandboxing.** Done when a deliberately malicious test app cannot read other apps, secrets or the open network.

- [ ] Container or bubblewrap per app; read-only filesystem except its data folder
- [ ] Granted DB files mounted read-only
- [ ] Egress proxy with the manifest allowlist
- [ ] CPU and memory limits; dependency allowlist
- [ ] Review against the security table

**M7 Self-host install.** Done when someone else installs on their own EC2 without your help. **Gate 3.**

- [ ] One-line install script; EC2 guide with Caddy; Mac mini guide
- [ ] Signed host image updates
- [ ] Encrypted backups with Litestream

### Stage 4 · Growth

**Gate 4:** people outside your circle install apps from the marketplace.

- [ ] **M8 Multi-instance:** link several instances, combined grid, choose and move an app's instance
- [ ] **M9 AI chat:** built-in chat on the LLM gateway that can also drive the build tools
- [ ] **M10 Marketplace:** central catalog, signed bundles, search, install with a permission prompt
- [ ] **M11 Rented servers:** the same image on your infra, provisioning, billing, onboarding

## Open questions

- [ ] Product name and domain (needed for per-app subdomains and the rented-instance offering).
- [ ] Multi-instance details: how app placement and moving apps between instances work in the PWA.
- [ ] Is the built-in AI chat service part of the MVP, or does Claude-based creation come first?
- [ ] Which Python packages go on the dependency allowlist for mini apps?
- [ ] OAuth requirements of Claude and ChatGPT custom connectors for the MCP endpoint (check current docs before M4).
- [ ] Monetization: open-source instance with paid hosting, marketplace revenue share, or both.
