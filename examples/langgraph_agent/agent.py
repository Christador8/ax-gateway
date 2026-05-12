#!/usr/bin/env python3
"""agent.py — LangGraph StateGraph invoked by `ax listen --exec` per @mention.

Two nodes: analyze (intent bullets) → respond (channel reply). Final text on stdout.
"""

from __future__ import annotations

import os
import sys
from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph


class GraphState(TypedDict):
    mention: str
    analysis: str
    reply: str


def _mention_content() -> str:
    if len(sys.argv) > 1:
        return str(sys.argv[-1]).strip()
    return (os.environ.get("AX_MENTION_CONTENT") or "").strip()


def _chat() -> ChatOpenAI:
    api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set")
    model = (os.environ.get("LANGGRAPH_MODEL") or "gpt-4o-mini").strip()
    kwargs: dict = {
        "model": model,
        "api_key": api_key,
        "temperature": 0,
    }
    base = (os.environ.get("OPENAI_API_BASE") or "").strip()
    if base:
        kwargs["base_url"] = base.rstrip("/")
    return ChatOpenAI(**kwargs)


def _analyze(state: GraphState) -> GraphState:
    llm = _chat()
    msg = llm.invoke(
        [
            SystemMessage(
                content="You extract intent from one chat @mention. Be brief.",
            ),
            HumanMessage(
                content=(
                    f"Message:\n---\n{state['mention']}\n---\n"
                    "Reply with 2–4 short bullet points only."
                ),
            ),
        ]
    )
    text = (msg.content or "").strip()
    return {**state, "analysis": text}


def _respond(state: GraphState) -> GraphState:
    llm = _chat()
    msg = llm.invoke(
        [
            SystemMessage(
                content=(
                    "You post as the aX agent. Plain text, under 2000 characters. "
                    "No chain-of-thought; only what users read in chat."
                ),
            ),
            HumanMessage(
                content=(
                    f"Original message:\n{state['mention']}\n\n"
                    f"Analysis:\n{state['analysis']}\n\n"
                    "Write the final reply."
                ),
            ),
        ]
    )
    text = (msg.content or "").strip()
    return {**state, "reply": text}


def _build_app():
    g = StateGraph(GraphState)
    g.add_node("analyze", _analyze)
    g.add_node("respond", _respond)
    g.set_entry_point("analyze")
    g.add_edge("analyze", "respond")
    g.add_edge("respond", END)
    return g.compile()


def main() -> int:
    content = _mention_content()
    if not content:
        print("(no mention content received)", file=sys.stderr)
        return 1

    if not (os.environ.get("OPENAI_API_KEY") or "").strip():
        print(
            "ERROR: OPENAI_API_KEY is not set. Add it to .env (see env.example).",
            file=sys.stderr,
        )
        return 1

    try:
        app = _build_app()
        out = app.invoke(
            {"mention": content, "analysis": "", "reply": ""},
        )
    except ImportError as e:
        print(
            f"ERROR: missing dependency ({e}). Run: pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 1
    except Exception as exc:
        print(f"ERROR: LangGraph run failed: {exc}", file=sys.stderr)
        return 1

    reply = (out.get("reply") or "").strip()
    if not reply:
        print("(agent produced no output)", file=sys.stderr)
        return 1
    print(reply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
