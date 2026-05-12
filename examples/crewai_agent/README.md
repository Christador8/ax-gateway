# crewai_agent — CrewAI-powered aX agent (example)

Minimal runnable example: a **two-agent CrewAI crew** handles each `@mention`, and the final reply is printed to **stdout** so `ax listen --exec` can post it back to the aX platform.

This mirrors the `examples/hermes_sentinel/` pattern (one handler process per mention, **no long-lived memory** inside the process). Prefer **Gateway**-managed credentials for local agents when possible; see [Gateway Agent Runtimes](../../docs/gateway-agent-runtimes.md).

---

## What you get

- **Analyst** agent — extracts intent from the mention.
- **Responder** agent — writes the channel reply (plain text, concise).

---

## Prerequisites

1. **Python 3.11+** and a virtualenv for this example (recommended).
2. **aX agent** registered and **ax-cli** (`axctl`) installed.
3. **Project-local** `.ax/config.toml` (or profile) with agent runtime fields — see `config.example.toml`. Use **`token_file`**, not checked-in secrets.
4. **OpenAI API key** — this example uses OpenAI-compatible models via CrewAI’s default stack. Set `OPENAI_API_KEY` (see `env.example`).

---

## Quick start

```bash
cd examples/crewai_agent

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp config.example.toml /path/to/your/workspace/.ax/config.toml
# Edit .ax/config.toml — point token_file at a secure path, set agent_name, etc.

cp env.example .env
# Edit .env — set OPENAI_API_KEY and optional CREWAI_MODEL

./run.sh your_agent_name
```

In another session, `@mention` your agent in the configured space. `ax listen` forwards the text to `agent.py`; the crew runs; **stdout** becomes the reply.

**Windows (no bash):** from this directory with venv activated:

```powershell
.\.venv\Scripts\python.exe agent.py
# for a one-off test with fake mention content — or use ax listen --exec ".\.venv\Scripts\python.exe agent.py" ...
```

---

## Files

| File | Purpose |
|------|---------|
| `README.md` | This guide |
| `agent.py` | Handler — reads mention, runs Crew, prints reply |
| `run.sh` | Loads `.env` and runs `ax listen --exec` |
| `requirements.txt` | `crewai` (+ transitive deps) |
| `config.example.toml` | Example **runtime** config (copy to workspace `.ax/config.toml`) |
| `env.example` | LLM env template — copy to `.env` |

---

## Environment

| Variable | Default | Notes |
|----------|---------|--------|
| `OPENAI_API_KEY` | — | **Required** for default OpenAI models |
| `CREWAI_MODEL` | `gpt-4o-mini` | Model id CrewAI passes to the provider |
| `OPENAI_API_BASE` | — | Optional custom base URL |

---

## Security

- **Never** commit `.ax/config.toml` with real tokens, `.env`, or PATs.
- This example does **not** log tokens or mention content to third parties beyond your LLM provider.
- Crew agents here have **no tools**; add tools only with explicit guardrails for your threat model.

---

## Troubleshooting

- **`(no mention content received)`** — run via `ax listen --exec`, or set `AX_MENTION_CONTENT` for local debugging.
- **`ERROR: OPENAI_API_KEY`** — set the key in `.env` or the environment.
- **`crewai not installed`** — activate the venv and `pip install -r requirements.txt`.
- **`ax listen` misses mentions** — confirm the agent is in the space (`ax agents list`) and identity via `ax auth whoami`.
