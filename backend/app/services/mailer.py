"""Email delivery via the Resend API. Requires RESEND_API_KEY in the environment."""
import resend

from ..config import settings

resend.api_key = settings.resend_api_key


def send_briefing(*, to: str, subject: str, html: str) -> str:
    """Returns the Resend message ID."""
    if not settings.resend_api_key:
        raise RuntimeError("RESEND_API_KEY is not configured")

    params: resend.Emails.SendParams = {
        "from": settings.from_email,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    response = resend.Emails.send(params)
    return response["id"]
