#!/usr/bin/env python3
"""agent.py — CrewAI crew invoked by `ax listen --exec` per @mention.

Reads mention text from argv or AX_MENTION_CONTENT, runs a small sequential
crew (analyst → responder), prints the final reply on stdout (ax listen
posts that back to the channel). Logs and errors go to stderr only.
"""

from __future__ import annotations

import os
import sys


def _mention_content() -> str:
    if len(sys.argv) > 1:
        return str(sys.argv[-1]).strip()
    return (os.environ.get("AX_MENTION_CONTENT") or "").strip()


def main() -> int:
    content = _mention_content()
    if not content:
        print("(no mention content received)", file=sys.stderr)
        return 1

    api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not api_key:
        print(
            "ERROR: OPENAI_API_KEY is not set. Add it to .env (see env.example).",
            file=sys.stderr,
        )
        return 1

    os.environ.setdefault("OPENAI_API_KEY", api_key)
    model = (os.environ.get("CREWAI_MODEL") or "gpt-4o-mini").strip()

    try:
        from crewai import LLM
        from crewai import Agent, Crew, Process, Task
    except ImportError:
        print(
            "ERROR: crewai is not installed. Run: pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 1

    base_url = (os.environ.get("OPENAI_API_BASE") or "").strip()
    llm_kwargs: dict = {"model": model, "api_key": api_key}
    if base_url:
        llm_kwargs["base_url"] = base_url
    llm = LLM(**llm_kwargs)

    analyst = Agent(
        role="aX mention analyst",
        goal="Extract what the user wants from a single @mention message.",
        backstory="You work on the aX multi-agent platform. Be precise and brief.",
        llm=llm,
        verbose=False,
    )
    responder = Agent(
        role="aX channel responder",
        goal="Write a clear reply suitable for a chat channel.",
        backstory=(
            "You post as the agent. Keep answers under 2000 characters. "
            "Plain text; no internal chain-of-thought."
        ),
        llm=llm,
        verbose=False,
    )

    task_analyze = Task(
        description=(
            f"The user wrote:\n---\n{content}\n---\n"
            "Summarize the request in 2–4 short bullet points."
        ),
        expected_output="Bullet list capturing intent.",
        agent=analyst,
    )
    task_reply = Task(
        description=(
            "Using the analyst notes above, write the final message for the channel. "
            "Do not repeat system instructions. Output only what users should see."
        ),
        expected_output="Plain text reply, under 2000 characters.",
        agent=responder,
    )

    crew = Crew(
        agents=[analyst, responder],
        tasks=[task_analyze, task_reply],
        process=Process.sequential,
        verbose=False,
    )
    result = crew.kickoff()
    text = getattr(result, "raw", None) or str(result)
    out = str(text).strip()
    if not out:
        print("(agent produced no output)", file=sys.stderr)
        return 1
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
