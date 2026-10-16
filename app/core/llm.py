
from google import genai
from google.genai import types

from app.core.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    validate_config,
)


SYSTEM_PROMPT = """
You are a professional customer support AI assistant.

Your responsibilities:
1. Answer customer questions clearly and politely.
2. Help with general product and service questions.
3. Explain troubleshooting steps when appropriate.
4. Ask clarifying questions when necessary.
5. Keep answers concise and easy to understand.
6. Never invent company policies, order details,
   refunds, delivery dates, or account information.
7. If information is unavailable, clearly say so.
8. Recommend human support when an issue requires
   account access or an authorized decision.
9. Do not claim to have created tickets, issued
   refunds, or performed external actions.
10. Do not ask for passwords, OTPs, or payment
    card details.

You are currently a general demonstration assistant.
A company knowledge base will be added later.
"""


def generate_ai_response(messages):
    validate_config()

    contents = []

    for message in messages:
        role = message.get("role")
        content = message.get("content", "").strip()

        if role not in ("user", "assistant"):
            continue

        if not content:
            continue

        gemini_role = (
            "model" if role == "assistant" else "user"
        )

        contents.append(
            types.Content(
                role=gemini_role,
                parts=[
                    types.Part.from_text(text=content)
                ],
            )
        )

    if not contents:
        raise ValueError("No messages provided.")

    if contents[-1].role != "user":
        raise ValueError(
            "The latest message must be from the user."
        )

    client = genai.Client(
        api_key=GEMINI_API_KEY,
        http_options=types.HttpOptions(
            timeout=30000
        ),
    )

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.3,
                max_output_tokens=1024,
            ),
        )

        answer = response.text

        if not answer or not answer.strip():
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return answer.strip()

    finally:
        client.close()
