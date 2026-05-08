"""Email delivery via the Resend API. Falls back to terminal output when RESEND_API_KEY is not set."""
import re

import resend

from ..config import settings

resend.api_key = settings.resend_api_key


def _strip_html(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html)


def send_briefing(*, to: str, subject: str, html: str) -> str:
    """Send briefing email. Prints to terminal instead when Resend is not configured."""
    if not settings.resend_api_key:
        plain = _strip_html(html).strip()
        plain = re.sub(r"\n{3,}", "\n\n", plain)
        border = "=" * 60
        print(f"\n{border}")
        print(f"TO:      {to}")
        print(f"SUBJECT: {subject}")
        print(border)
        print(plain)
        print(f"{border}\n")
        return "mock-message-id"

    params: resend.Emails.SendParams = {
        "from": settings.from_email,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    response = resend.Emails.send(params)
    return response["id"]
