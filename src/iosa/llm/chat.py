"""Call Ollama's chat endpoint to get an LLM text response.

Shared by every reasoning node in the agent (router, grade, rewrite,
generate), each passes its own prompt and system message. This module
has no task-specific logic, it is purely a thin wrapper around the
HTTP call, same pattern as embedder.py for embeddings.
"""
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen2.5:7b-instruct")


def chat(prompt: str, system: str = "", temperature: float = 0.0) -> str:
    """Send a prompt to the chat model, return its text reply.

    temperature=0.0 by default for deterministic, reproducible behavior,
    important for grading and routing decisions where we want consistent
    yes/no judgments rather than creative variation.
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = httpx.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model": CHAT_MODEL,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        },
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]