"""hello_llm.py: one real call to a hosted LLM, with the key read from .env.

    python hello_llm.py
    python hello_llm.py "Explain a virtual environment in one sentence."

The key never appears in code, in arguments or in output: python-dotenv loads it
from .env (which git ignores) into the environment, and the OpenAI client reads it there.
"""

from __future__ import annotations

import os
import sys
import time

from dotenv import load_dotenv
from openai import OpenAI

DEFAULT_QUESTION = "In one sentence: what does a forward deployed engineer do?"


def main() -> int:
    load_dotenv()  # reads .env in the current folder; real environment variables win
    key = os.getenv("NVIDIA_API_KEY", "")
    if not key.startswith("nvapi-"):
        print("NVIDIA_API_KEY is missing. Copy .env.example to .env and paste your key.", file=sys.stderr)
        return 1

    client = OpenAI(
        base_url=os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"),
        api_key=key,
        timeout=60,
        max_retries=2,
    )
    model = os.getenv("CHAT_MODEL", "openai/gpt-oss-20b")
    question = " ".join(sys.argv[1:]) or DEFAULT_QUESTION

    print(f"model    : {model}")
    print(f"question : {question}")
    t0 = time.perf_counter()
    reply = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": question}],
        max_tokens=600,
        temperature=0.2,
    )
    seconds = time.perf_counter() - t0
    answer = (reply.choices[0].message.content or "").strip()
    usage = reply.usage
    print(f"answer   : {answer}")
    if usage:
        print(f"tokens   : {usage.prompt_tokens} in, {usage.completion_tokens} out")
    print(f"latency  : {seconds:.1f} s")
    return 0 if answer else 1


if __name__ == "__main__":
    sys.exit(main())
