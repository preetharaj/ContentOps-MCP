"""
Webhook endpoints for Content-ops Orchestrator.
Optional for Day 3; provides alternative to polling.
Stub for future use (e.g., Notion webhooks, Slack events).
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
import logging

from backend.database import get_db
from backend.models.workflow import Workflow
from backend.engine.runner import run_workflow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/notion")
async def notion_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook endpoint for Notion events.
    
    Notion can push events here instead of polling.
    Signature verification should be added in production.
    
    Returns:
        {"status": "ok"}
    """
    try:
        payload = await request.json()
        logger.info(f"Received Notion webhook: {payload}")
        
        # TODO: Verify Notion signature (see Notion docs)
        # TODO: Extract trigger event from payload
        # TODO: Find matching workflows and call run_workflow()
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"Error processing Notion webhook: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/slack")
async def slack_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook endpoint for Slack events.
    (e.g., button clicks, slash commands)
    
    Stub for future use.
    
    Returns:
        {"status": "ok"}
    """
    try:
        payload = await request.json()
        logger.info(f"Received Slack webhook: {payload}")
        
        # TODO: Handle Slack events
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"Error processing Slack webhook: {e}")
        raise HTTPException(status_code=400, detail=str(e))
