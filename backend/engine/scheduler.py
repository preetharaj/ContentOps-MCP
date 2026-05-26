"""
Scheduler: periodically polls triggers and executes workflows.
Runs in a background thread/task.
"""

import logging
import schedule
import time
import threading
from typing import Optional

from backend.database import SessionLocal
from backend.triggers.notion import poll_notion_pages
from backend.models.workflow import Workflow
from backend.engine.runner import run_workflow

logger = logging.getLogger(__name__)

_scheduler_thread: Optional[threading.Thread] = None
_scheduler_running = False

def schedule_job():
    """
    Scheduled job that polls Notion and triggers workflows.
    """
    logger.debug("Running scheduler job...")
    
    db = SessionLocal()
    try:
        # Poll Notion for new pages
        trigger_events = poll_notion_pages(db)
        
        if not trigger_events:
            logger.debug("No new Notion pages detected")
            return
        
        logger.info(f"Detected {len(trigger_events)} new Notion page(s)")
        
        # Find workflows with Notion trigger
        workflows = db.query(Workflow).filter(
            Workflow.is_enabled == True
        ).all()
        
        for workflow in workflows:
            trigger_config = workflow.trigger
            
            # Check if this workflow listens to Notion triggers
            if trigger_config.get("app") == "notion":
                for event in trigger_events:
                    if event["event"] == trigger_config.get("event", "page_created"):
                        # Run the workflow
                        logger.info(f"Triggering workflow {workflow.id} from Notion event")
                        run_workflow(workflow.id, event, db)
    
    except Exception as e:
        logger.error(f"Error in scheduler job: {e}")
    
    finally:
        db.close()

def scheduler_worker():
    """
    Background worker that runs scheduled jobs.
    """
    global _scheduler_running
    
    # Schedule the job to run every 30 seconds (can adjust)
    schedule.every(30).seconds.do(schedule_job)
    
    logger.info("Scheduler worker started")
    
    while _scheduler_running:
        schedule.run_pending()
        time.sleep(1)
    
    logger.info("Scheduler worker stopped")

def start_scheduler():
    """Start the background scheduler thread."""
    global _scheduler_thread, _scheduler_running
    
    if _scheduler_running:
        logger.warning("Scheduler already running")
        return
    
    _scheduler_running = True
    _scheduler_thread = threading.Thread(target=scheduler_worker, daemon=True)
    _scheduler_thread.start()
    logger.info("Scheduler started in background thread")

def stop_scheduler():
    """Stop the background scheduler thread."""
    global _scheduler_running
    
    _scheduler_running = False
    if _scheduler_thread:
        _scheduler_thread.join(timeout=5)
    logger.info("Scheduler stopped")
