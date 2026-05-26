"""
Slack step implementation.
Sends notifications to Slack channels via webhook.
"""

import os
import logging
from typing import Dict, Any
import httpx

logger = logging.getLogger(__name__)

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

async def notify_team(
    draft_url: str,
    title: str = "",
    author: str = "",
    **kwargs
) -> Dict[str, Any]:
    """
    Send a notification to Slack about a new draft.
    
    Args:
        draft_url: URL of the blog draft
        title: Draft title
        author: Author name
        **kwargs: Additional parameters from Step.parameters
    
    Returns:
        Dictionary with delivery status
    """
    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL not configured, skipping Slack notification")
        return {
            "status": "skipped",
            "message": "Slack webhook not configured",
        }
    
    try:
        # Build Slack message
        message = {
            "text": f"📝 New blog draft from {author or 'Unknown'}" if author else "📝 New blog draft",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*New Draft: {title or 'Untitled'}*\n_by {author or 'Unknown'}_"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"<{draft_url}|View Draft>"
                    }
                },
                {
                    "type": "divider"
                }
            ]
        }
        
        # Send to Slack webhook
        async with httpx.AsyncClient() as client:
            response = await client.post(
                SLACK_WEBHOOK_URL,
                json=message,
                timeout=10.0
            )
            response.raise_for_status()
        
        logger.info(f"Sent Slack notification for draft: {draft_url}")
        
        return {
            "status": "success",
            "draft_url": draft_url,
            "message": "Notification sent to Slack",
        }
    
    except Exception as e:
        logger.error(f"Error sending Slack notification: {e}")
        return {
            "status": "error",
            "error": str(e),
        }
