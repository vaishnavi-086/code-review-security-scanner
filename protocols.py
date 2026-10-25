import os

from openai import OpenAI
from uagents import Context
from uagents.experimental.chat_agent.protocol import build_llm_message_history

client = OpenAI(
    base_url=os.environ["ASI1_BASE_URL"],
    api_key=os.environ["ASI1_API_KEY"],
)

INTAKE_PROMPT = (
    "You are Stage 1 (Intake) of a code review pipeline. Normalize the user's input into a "
    "clear review request: identify the language, list files/sections changed, and restate "
    "what needs review. If the input is not code or a review request, say so briefly."
)

SCAN_PROMPT = (
    "You are Stage 2 (Security & Bug Scanner). Given the normalized review request below, "
    "produce a numbered list of findings. For each: severity (critical/high/medium/low), "
    "category (security or bug), the exact code location or snippet, and a one-line explanation. "
    "Look for: injection, hardcoded secrets, insecure auth, unsafe deserialization, race "
    "conditions, logic errors, missing error handling, and resource leaks. If none found, say so."
)

SUMMARY_PROMPT = (
    "You are Stage 3 (Review Summarizer). Given the findings below, write a concise review: "
    "1) an overall risk verdict in one sentence, 2) the key findings grouped by severity, and "
    "3) prioritized actionable recommendations as a short numbered list. Be direct and concrete."
)


def _run_stage(system_prompt: str, payload: str) -> str:
    completion = client.chat.completions.create(
        model="asi1",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": payload},
        ],
        max_tokens=2048,
    )
    return completion.choices[0].message.content or ""


async def handle_review_request(ctx: Context, sender: str, text: str) -> str:
    try:
        intake = _run_stage(INTAKE_PROMPT, text)
        findings = _run_stage(SCAN_PROMPT, intake)
        summary = _run_stage(SUMMARY_PROMPT, findings)
        return (
            "=== Code Review Report ===\n\n"
            "--- Intake ---\n"
            f"{intake.strip()}\n\n"
            "--- Findings ---\n"
            f"{findings.strip()}\n\n"
            "--- Summary & Recommendations ---\n"
            f"{summary.strip()}"
        )
    except Exception as e:
        ctx.logger.exception("Review pipeline failed")
        return f"The review pipeline failed while processing your request. Please try again. ({e})"
