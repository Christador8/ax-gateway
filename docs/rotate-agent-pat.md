# Rotate an agent PAT

This guide is for operators who run agents with a **agent-scoped PAT** (personal access token) and need to replace it safely—after suspicion of leak, as part of policy, or before decommissioning an old key.

Rotation means: **a new credential works everywhere the agent runs**, and **the old credential is revoked** only after you have verified the replacement.

Never paste tokens into tickets, chat logs, or public repositories. Prefer a `token_file` with mode `600` instead of inline `token` in config when you can.

## Why rotation matters

- **Leak or exposure** — If a token might have been copied, rotation limits how long it remains useful.
- **Offboarding** — Revoking scoped keys is part of shutting down an automation or agent identity.
- **Policy** — Some teams require periodic rotation or rotation after personnel changes.

The aX platform ties activity to **credential IDs**. Rotating creates a new secret while you control exactly when the old one stops working.

## Prerequisites

- **User bootstrap** — You need a session that is allowed to manage keys for the agent (typically your user login and `ax keys` commands), not only the agent runtime token alone.
- **Know your agent** — Have `agent_name`, `agent_id`, and `space_id` consistent with the running agent (see `ax auth whoami` before rotation).
- **Inventory** — List keys and note the **credential ID** of the PAT you are replacing:

  ```bash
  ax keys list --json
  ```

## Path A — Rotate in place (same credential row)

When you already have the **credential ID** of the agent PAT and the API supports rotation for that row:

```bash
ax keys rotate <credential-id> --json
```

The CLI prints (or JSON includes) the **new** secret **once**. Copy it into your secret store or token file immediately, then update runtime config (next section). The old secret for that credential should stop working after a successful rotate.

If you are not using `--json`, read the token from the interactive output once and store it securely.

## Path B — Create a replacement key (overlap window)

Use this when you want a **new** credential alongside the old one until you have verified the new one.

1. Mint a new scoped key for the same agent (repeat `--scope-to-agent` for each UUID if you use multiple):

   ```bash
   ax keys create --name "orion-runtime-2026-05" --scope-to-agent <agent-uuid> --json
   ```

2. Save the token to a file with restrictive permissions (Unix example):

   ```bash
   umask 077
   printf '%s' '<paste-token-here>' > ~/.ax/agents/orion_token_new
   chmod 600 ~/.ax/agents/orion_token_new
   ```

3. Point the agent runtime at the new secret (below), run your agent or CI check, then revoke the old credential ID with `ax keys revoke`.

Do **not** revoke the old key until the new one is verified.

## Update runtime config

The CLI resolves credentials in a fixed order (flags → env → project **`.ax/config.toml`** → active **profile** → global `~/.ax/config.toml`). Update **one** place—the one your process actually uses.

### Project-local `.ax/config.toml`

Update either:

- `token_file` — recommended: path to a file that contains only the new token, or
- `token` — only when you must inline it temporarily; prefer moving to `token_file` afterward.

Keep `base_url`, `agent_name`, `agent_id`, and `space_id` aligned with the agent identity. Do not commit `.ax/config.toml` if it contains secrets; it should already be in `.gitignore` for agent workspaces.

### Named profile (`~/.ax/profiles/<name>/profile.toml`)

Profiles bind the token file fingerprint, host, and working directory. After you replace the token file contents, **rebind** the profile so fingerprints match:

```bash
ax profile add <profile-name> \
  --url https://paxai.app \
  --token-file ~/.ax/agents/orion_token \
  --agent-name <agent_name>

ax profile use <profile-name>
ax profile verify
```

Adjust flags to match how you originally created the profile (`--agent-id`, space options, etc.—see `ax profile add --help`).

## Verify

From the same working directory and environment the agent will use:

```bash
ax auth whoami --json
```

Confirm `principal_type`, `bound_agent` / resolved agent fields, and space context match what you expect. Run a harmless command your agent uses (for example a read-only listing) before revoking the old PAT.

## Revoke the old key

After verification:

```bash
ax keys revoke <old-credential-id>
```

If you used **Path A** (`ax keys rotate`), revocation of the old secret may already be handled by the platform; still confirm in `ax keys list --json` that only the intended credentials remain active.

## Gateway-brokered agents

If the agent uses **Gateway** (`ax gateway local connect` and managed tokens under `~/.ax/gateway/...`), prefer rotating through Gateway and user approval flows documented in [Agent authentication](agent-authentication.md). This document focuses on **direct** agent PATs and profiles.

## See also

- [Agent authentication](agent-authentication.md) — bootstrap paths, profiles, and lifecycle overview
- [Credential security](credential-security.md) — fingerprinting and safe handling
