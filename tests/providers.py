"""LLM provider backends for e2e tests.

Select via E2E_PROVIDER env var: anthropic, gemini, deepseek, groq, claude-cli.
Default: gemini (free tier available).
"""

import os
import subprocess
import time


MAX_TOKENS = 65536
TIMEOUT = 180
MAX_RETRIES = 3
INITIAL_DELAY = 10

# The model each provider calls: the environment variable that overrides
# it, and the default. A report names the model it graded, so the runner
# reads the choice from here rather than each backend keeping its own.
MODELS = {
    "anthropic": ("ANTHROPIC_MODEL", "claude-opus-5"),
    "gemini": ("GEMINI_MODEL", "gemini-2.5-flash"),
    "deepseek": ("DEEPSEEK_MODEL", "deepseek-chat"),
    "groq": ("GROQ_MODEL", "llama-3.3-70b-versatile"),
}


def model_for(name):
    """Return the model a provider will call, as the run is configured."""
    if name not in MODELS:
        return "the CLI's configured model"
    variable, default = MODELS[name]
    return os.environ.get(variable, default)


def _anthropic(prompt):
    """Call Anthropic Messages API. Requires ANTHROPIC_API_KEY."""
    import anthropic
    client = anthropic.Anthropic()

    # Current models reject sampling parameters and think by default, so
    # send none and join the text blocks rather than reading the first
    # block. The output ceiling needs a stream: the SDK declines a
    # non-streaming request this large as one that would outrun its timeout.
    with client.messages.stream(
        model=model_for("anthropic"),
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        message = stream.get_final_message()

    # A refusal or a truncated answer is not an output to grade, and
    # asserting against it would report a template defect that is not there.
    if message.stop_reason != "end_turn":
        raise RuntimeError(f"stopped on {message.stop_reason}, not end_turn")
    return "".join(b.text for b in message.content if b.type == "text")


def _gemini(prompt):
    """Call Google Gemini API. Requires GEMINI_API_KEY."""
    from google import genai
    model = model_for("gemini")
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={"max_output_tokens": MAX_TOKENS, "temperature": 0},
    )
    return response.text


def _deepseek(prompt):
    """Call DeepSeek API. Requires DEEPSEEK_API_KEY."""
    from openai import OpenAI
    model = model_for("deepseek")
    client = OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com",
    )
    response = client.chat.completions.create(
        model=model,
        max_tokens=MAX_TOKENS,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def _groq(prompt):
    """Call Groq API. Requires GROQ_API_KEY."""
    from groq import Groq
    model = model_for("groq")
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    response = client.chat.completions.create(
        model=model,
        max_tokens=min(MAX_TOKENS, 32768),
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def _claude_cli(prompt):
    """Call Claude via CLI. Uses Pro subscription, no API credits."""
    result = subprocess.run(
        "claude -p --no-session-persistence",
        input=prompt,
        capture_output=True,
        timeout=TIMEOUT,
        encoding="utf-8",
        errors="replace",
        shell=True,
    )
    if not result.stdout.strip():
        raise RuntimeError(
            "claude CLI returned empty output — "
            "check that Claude Code is installed and authenticated"
        )
    return result.stdout


PROVIDERS = {
    "anthropic": _anthropic,
    "gemini": _gemini,
    "deepseek": _deepseek,
    "groq": _groq,
    "claude-cli": _claude_cli,
}

DEFAULT_PROVIDER = "gemini"


def _is_rate_limit(exc):
    """Check if an exception is a rate limit or temporary overload."""
    msg = str(exc).lower()
    return any(k in msg for k in ("429", "503", "rate", "overloaded", "unavailable"))


def _with_retry(fn):
    """Wrap a provider function with exponential backoff on rate limits."""
    def wrapper(prompt):
        delay = INITIAL_DELAY
        for attempt in range(MAX_RETRIES + 1):
            try:
                return fn(prompt)
            except Exception as exc:
                if attempt < MAX_RETRIES and _is_rate_limit(exc):
                    print(f"  rate limited, retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise
    return wrapper


def get_provider():
    """Return the configured provider function (with retry)."""
    name = os.environ.get("E2E_PROVIDER", DEFAULT_PROVIDER)
    if name not in PROVIDERS:
        raise ValueError(
            f"Unknown E2E_PROVIDER={name!r}. "
            f"Options: {', '.join(PROVIDERS)}"
        )
    return name, _with_retry(PROVIDERS[name])
