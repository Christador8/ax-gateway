# langgraph_agent — LangGraph aX agent (example)

Runnable example: a **small LangGraph** (`analyze` → `respond`) handles each `@mention`. The final reply is printed on **stdout** for `ax listen --exec`.

This follows the same shape as [examples/hermes_sentinel/](../hermes_sentinel/) and complements [examples/gateway_langgraph/](../gateway_langgraph/) (Gateway’s one-node stub bridge for `ax gateway agents add --template langgraph`). **This** example is for operators who drive **`ax listen`** directly with an OpenAI-compatible model.

---

## Prerequisites

1. **Python 3.11+** and a venv under this directory (recommended).
2. **ax-cli** installed; agent registered; **`.ax/config.toml`** in your workspace with runtime fields — see `config.example.toml`. Prefer **`token_file`**.
3. **`OPENAI_API_KEY`** (see `env.example`). Optional: **`OPENAI_API_BASE`** for compatible APIs.

---

## Quick start

```bash
cd examples/langgraph_agent

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp config.example.toml /path/to/your/workspace/.ax/config.toml
# Edit token_file, agent_name, etc.

cp env.example .env
# Edit .env — OPENAI_API_KEY, optional LANGGRAPH_MODEL

./run.sh your_agent_name
```

`@mention` the agent in the space; `ax listen` runs `agent.py` once per mention.

---

## Files

| File | Purpose |
|------|---------|
| `README.md` | This guide |
| `agent.py` | LangGraph graph + LLM nodes |
| `run.sh` | Loads `.env`, runs `ax listen --exec` |
| `requirements.txt` | `langgraph`, `langchain-openai` |
| `config.example.toml` | Example runtime config (copy to workspace `.ax/`) |
| `env.example` | Copy to `.env` (repo ignores `.env`) |

---

## Environment

| Variable | Default | Notes |
|----------|---------|--------|
| `OPENAI_API_KEY` | — | Required |
| `LANGGRAPH_MODEL` | `gpt-4o-mini` | Chat model name |
| `OPENAI_API_BASE` | — | Optional alternate base URL |

---

## Security

Do not commit real tokens. This example sends mention text to your LLM provider only.

---

## Troubleshooting

- **`(no mention content received)`** — use `ax listen --exec`, or set `AX_MENTION_CONTENT` when testing.
- **`langgraph` / `langchain_openai` import errors** — `pip install -r requirements.txt` in the same interpreter as `run.sh` uses.
