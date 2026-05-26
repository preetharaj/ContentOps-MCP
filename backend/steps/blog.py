"""
Blog step implementation.
Handles draft creation and publishing.
"""

import os
import logging
import uuid
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

BLOG_BASE_URL = os.getenv("BLOG_BASE_URL", "http://contentops.local")
BLOG_API_KEY = os.getenv("BLOG_API_KEY", "mock_key")

async def create_draft(
    title: str,
    brief: str = "",
    author: str = "",
    **kwargs
) -> Dict[str, Any]:
    """
    Create a blog draft.
    
    Args:
        title: Draft title
        brief: Brief description/outline
        author: Author name
        **kwargs: Additional parameters from Step.parameters
    
    Returns:
        Dictionary with draft_url and metadata
    """
    try:
        # For MVP, mock the blog API response
        # In Phase 2, integrate with real blog platform (Hashnode, Dev.to, etc.)
        
        draft_id = str(uuid.uuid4())[:8]
        draft_url = f"{BLOG_BASE_URL}/drafts/{draft_id}"
        
        logger.info(f"Created blog draft: {draft_url}")
        
        return {
            "status": "success",
            "draft_url": draft_url,
            "draft_id": draft_id,
            "title": title,
            "brief": brief,
            "author": author,
        }
    
    except Exception as e:
        logger.error(f"Error creating blog draft: {e}")
        return {
            "status": "error",
            "error": str(e),
        }

async def publish_draft(
    draft_url: str,
    draft_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Publish a blog draft.
    
    Args:
        draft_url: URL of the draft to publish
        draft_id: Optional draft ID for publishing
        **kwargs: Additional parameters from Step.parameters
    
    Returns:
        Dictionary with published_url and metadata
    """
    try:
        # For MVP, mock the publish API response
        
        published_url = draft_url.replace("/drafts/", "/posts/")
        
        logger.info(f"Published blog post: {published_url}")
        
        return {
            "status": "success",
            "published_url": published_url,
            "draft_url": draft_url,
        }
    
    except Exception as e:
        logger.error(f"Error publishing blog draft: {e}")
        return {
            "status": "error",
            "error": str(e),
        }
