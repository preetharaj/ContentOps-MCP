"""
Email step implementation.
Sends summary emails via Resend.
"""

import os
import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


async def send_summary(
    draft_url: str,
    email: Optional[str] = None,
    status: str = "draft",
    title: str = "",
    author: str = "",
    **kwargs
) -> Dict[str, Any]:

    api_key = os.getenv("EMAIL_SERVICE_API_KEY")
    email_from = os.getenv("EMAIL_FROM", "onboarding@resend.dev")
    email_to = email or os.getenv("EMAIL_TO") or os.getenv("RECIPIENT_EMAIL")

    print("-" * 80)
    print("[EMAIL] send_summary started")
    print("[EMAIL] EMAIL_SERVICE_API_KEY exists:", bool(api_key))
    print("[EMAIL] EMAIL_FROM:", email_from)
    print("[EMAIL] EMAIL_TO:", email_to)
    print("[EMAIL] draft_url:", draft_url)
    print("[EMAIL] title:", title)
    print("[EMAIL] status:", status)

    if not api_key:
        return {
            "status": "error",
            "error": "EMAIL_SERVICE_API_KEY is missing in .env",
        }

    if not email_to:
        return {
            "status": "error",
            "error": "EMAIL_TO is missing in .env",
        }

    try:
        subject = f"📝 Draft Ready for Review: {title or 'Untitled'}"

        body_text = (
            f"Your article '{title or 'Untitled'}' by {author or 'Unknown'} "
            f"is ready for review.\n\n"
            f"Review it here: {draft_url}"
        )

        body_html = f"""
<html>
<body>
<h2>📝 Draft Ready for Review</h2>
<p>Your article <strong>{title or 'Untitled'}</strong> by <em>{author or 'Unknown'}</em> is ready for review.</p>
<p><a href="{draft_url}">Review the draft</a></p>
</body>
</html>
"""

        payload = {
            "from": email_from,
            "to": [email_to],
            "subject": subject,
            "html": body_html,
            "text": body_text,
        }

        print("[EMAIL] Sending request to Resend...")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                RESEND_API_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )

        print("[EMAIL] Resend status code:", response.status_code)
        print("[EMAIL] Resend response:", response.text)

        response.raise_for_status()
        result = response.json()

        print("[EMAIL] Email sent successfully")
        print("[EMAIL] Resend email id:", result.get("id"))

        return {
            "status": "success",
            "email": email_to,
            "draft_url": draft_url,
            "message": f"Email sent to {email_to}",
            "email_id": result.get("id", ""),
        }

    except Exception as e:
        print("[EMAIL] Error sending email:", str(e))
        logger.error(f"Error sending email: {e}")

        return {
            "status": "error",
            "error": str(e),
            "email": email_to,
        }