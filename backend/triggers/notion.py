"""
Notion trigger implementation.
Polls the Notion database for new pages and triggers workflows.
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any
from notion_client import Client

logger = logging.getLogger(__name__)

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# Simple in-memory tracking of processed pages (in production, use database)
_processed_pages = set()

def get_notion_client():
    """Initialize and return Notion client."""
    if not NOTION_API_KEY:
        raise ValueError("NOTION_API_KEY environment variable not set")
    return Client(auth=NOTION_API_KEY)

def poll_notion_pages(db_session=None) -> List[Dict[str, Any]]:
    """
    Poll the Notion database for new pages.
    Returns list of trigger events for each new page.
    
    Args:
        db_session: Optional SQLAlchemy session for persistence.
    
    Returns:
        List of trigger event dictionaries.
    """
    if not NOTION_DATABASE_ID:
        logger.warning("NOTION_DATABASE_ID not configured, skipping poll")
        return []

    try:
        client = get_notion_client()
        
        # Query database for pages
        response = client.databases.query(
            database_id=NOTION_DATABASE_ID
        )
        
        trigger_events = []
        for page in response.get("results", []):
            page_id = page["id"]
            
            # Skip if already processed
            if page_id in _processed_pages:
                continue
            
            # Mark as processed
            _processed_pages.add(page_id)
            
            # Convert page to trigger event
            trigger_event = convert_page_to_trigger_event(page)
            trigger_events.append(trigger_event)
            
            logger.info(f"Detected new Notion page: {page_id}")
        
        return trigger_events
    
    except Exception as e:
        logger.error(f"Error polling Notion: {e}")
        return []

def convert_page_to_trigger_event(page: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a Notion page to a trigger event.
    Extracts title, brief, and author from page properties.
    
    Args:
        page: Notion page object from API response.
    
    Returns:
        Trigger event dictionary.
    """
    page_id = page["id"]
    properties = page.get("properties", {})
    
    # Extract common properties (adjust to match your Notion schema)
    title = "Untitled"
    brief = ""
    author = ""
    
    # Try to extract title from "Title" property
    if "Title" in properties:
        title_prop = properties["Title"]
        if title_prop["type"] == "title":
            title_list = title_prop.get("title", [])
            if title_list:
                title = title_list[0].get("plain_text", "Untitled")
    
    # Try to extract brief from "Brief" or "Description" property
    if "Brief" in properties:
        brief_prop = properties["Brief"]
        if brief_prop["type"] == "rich_text":
            brief_list = brief_prop.get("rich_text", [])
            if brief_list:
                brief = brief_list[0].get("plain_text", "")
    
    # Try to extract author from "Author" property
    if "Author" in properties:
        author_prop = properties["Author"]
        if author_prop["type"] == "rich_text":
            author_list = author_prop.get("rich_text", [])
            if author_list:
                author = author_list[0].get("plain_text", "")
    
    return {
        "app": "notion",
        "event": "page_created",
        "config": {
            "page_id": page_id,
            "title": title,
            "brief": brief,
            "author": author,
            "created_at": page.get("created_time", datetime.utcnow().isoformat()),
        }
    }
