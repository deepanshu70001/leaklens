"""
Groq client — thin wrapper around Groq chat completions API (OpenAI-compatible).
Strict timeout + graceful fallback on failure per §7.
"""
import json
import httpx
from typing import Optional
from app.config import settings
from app.utils.pii_redaction import redact_pii


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


async def _call_groq(
    messages: list[dict],
    model: str,
    temperature: float = 0.3,
    max_tokens: int = 256,
) -> Optional[str]:
    """
    Make a chat completion call to Groq.
    Returns the response content string, or None on any failure.
    """
    if not settings.GROQ_API_KEY:
        return None

    try:
        async with httpx.AsyncClient(timeout=settings.GROQ_TIMEOUT_SECONDS) as client:
            response = await client.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                print(f"Groq API error: {response.status_code} — {response.text[:200]}")
                return None
    except (httpx.TimeoutException, httpx.ConnectError, Exception) as e:
        print(f"Groq API call failed: {type(e).__name__}: {e}")
        return None


async def extract_transaction_from_text(raw_text: str) -> Optional[dict]:
    """
    Extraction fallback: parse one line of SMS/email text via Groq.
    PII is redacted before sending. Returns parsed dict or None.
    """
    redacted = redact_pii(raw_text)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a financial transaction parser. Given one line of raw SMS or email "
                "text, extract merchant name, amount, currency, and date if present. Return ONLY a "
                'JSON object: {"merchant": string|null, "amount": number|null, "currency": string|null, '
                '"date": string|null}. Do not invent values you cannot find. No prose, no markdown.'
            ),
        },
        {"role": "user", "content": redacted},
    ]

    result = await _call_groq(
        messages=messages,
        model=settings.GROQ_EXTRACTION_MODEL,
        temperature=0.1,
        max_tokens=128,
    )

    if result:
        try:
            # Strip markdown code blocks if present
            cleaned = result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
                cleaned = cleaned.rsplit("```", 1)[0]
            return json.loads(cleaned)
        except (json.JSONDecodeError, IndexError):
            return None
    return None


async def generate_recommendation_reason(
    merchant: str,
    recommendation: str,
    days_unused: int,
    price_increase_pct: float,
    redundant_with: str,
) -> str:
    """
    Generate a plain-language recommendation reason via Groq.
    Falls back to a static template if Groq fails.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are a concise personal finance assistant. Given a subscription's leak "
                "score components, write ONE plain-language sentence (max 25 words) explaining the "
                "recommended action to a non-technical user. No jargon, no exclamation marks."
            ),
        },
        {
            "role": "user",
            "content": (
                f"merchant={merchant}, recommendation={recommendation}, days_unused={days_unused}, "
                f"price_increase_pct={price_increase_pct}, redundant_with={redundant_with}"
            ),
        },
    ]

    result = await _call_groq(
        messages=messages,
        model=settings.GROQ_REASONING_MODEL,
        temperature=0.5,
        max_tokens=64,
    )

    if result:
        return result

    # Static fallback
    return _static_recommendation_reason(merchant, recommendation, days_unused, price_increase_pct, redundant_with)


def _static_recommendation_reason(
    merchant: str,
    recommendation: str,
    days_unused: int,
    price_increase_pct: float,
    redundant_with: str,
) -> str:
    """Static fallback recommendation reasons when Groq is unavailable."""
    if recommendation == "cancel":
        if days_unused > 60:
            return f"You haven't used {merchant} in {days_unused} days. Consider canceling to save money."
        if price_increase_pct > 20:
            return f"{merchant} increased its price by {price_increase_pct:.0f}%. Consider canceling if the value doesn't match."
        return f"{merchant} has a high leak score. Review whether you still need this subscription."
    elif recommendation == "renegotiate":
        if price_increase_pct > 0:
            return f"{merchant} raised prices by {price_increase_pct:.0f}%. Contact support to negotiate a better rate."
        return f"You may be able to get a better deal on {merchant} by contacting their support team."
    elif recommendation == "downgrade":
        if redundant_with:
            return f"You have overlapping services with {redundant_with}. Consider downgrading {merchant} to a lower tier."
        return f"A lower-tier plan for {merchant} might cover your needs and save money."
    else:
        return f"{merchant} appears to provide good value for its cost. Keep it for now."


async def generate_negotiation_script(
    merchant: str,
    action: str,
    amount: float,
    tenure_months: int,
    reason: str,
) -> str:
    """
    Generate a cancellation/negotiation message draft via Groq.
    Falls back to a template if Groq fails.
    """
    messages = [
        {
            "role": "system",
            "content": (
                f"Draft a short, polite message (under 80 words) the user could send to "
                f"{merchant} customer support to {action} their subscription. Neutral, factual tone."
            ),
        },
        {
            "role": "user",
            "content": (
                f"subscription_amount={amount}, tenure_months={tenure_months}, reason={reason}"
            ),
        },
    ]

    result = await _call_groq(
        messages=messages,
        model=settings.GROQ_REASONING_MODEL,
        temperature=0.6,
        max_tokens=150,
    )

    if result:
        return result

    # Static fallback
    return (
        f"Hi {merchant} support team,\n\n"
        f"I've been a subscriber for {tenure_months} months. "
        f"I'd like to {action} my subscription (currently at {amount}/month). "
        f"{'I am looking for a better rate that reflects my loyalty as a long-term customer.' if action == 'renegotiate' else 'Please process this request at your earliest convenience.'}\n\n"
        f"Thank you for your assistance.\n"
        f"Best regards"
    )
