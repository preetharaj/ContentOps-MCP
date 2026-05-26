"""
FastAPI routes for Content-ops Orchestrator.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.models.workflow import Workflow
from backend.models.step import Step
from backend.models.run import Run
from backend.web.schemas import (
    WorkflowCreateSchema,
    WorkflowSchema,
    RunSchema,
    TriggerWorkflowSchema,
)
from backend.engine.runner import run_workflow

router = APIRouter(prefix="/api", tags=["workflows"])


@router.get("/workflows", response_model=List[WorkflowSchema])
def get_workflows(db: Session = Depends(get_db)):
    workflows = db.query(Workflow).all()
    return workflows


@router.post("/workflows", response_model=WorkflowSchema)
def create_workflow(payload: WorkflowCreateSchema, db: Session = Depends(get_db)):
    existing = db.query(Workflow).filter(Workflow.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Workflow with this name already exists")

    workflow = Workflow(
        name=payload.name,
        is_enabled=payload.is_enabled,
        trigger=payload.trigger.dict(),
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    for step in payload.steps:
        db_step = Step(
            workflow_id=workflow.id,
            app=step.app,
            action=step.action,
            parameters=step.parameters or {},
        )
        db.add(db_step)

    db.commit()
    db.refresh(workflow)

    print(f"[API] Created workflow: {workflow.name} | id={workflow.id}")
    return workflow


@router.get("/runs", response_model=List[RunSchema])
def get_runs(workflow_id: int = None, db: Session = Depends(get_db)):
    query = db.query(Run)
    if workflow_id:
        query = query.filter(Run.workflow_id == workflow_id)

    runs = query.order_by(Run.id.desc()).all()
    return runs


@router.post("/trigger", response_model=RunSchema)
def trigger_workflow(payload: TriggerWorkflowSchema, db: Session = Depends(get_db)):
    print("=" * 80)
    print("[API] Manual trigger received")
    print(f"[API] workflow_id={payload.workflow_id}")
    print("=" * 80)

    workflow = db.query(Workflow).filter(Workflow.id == payload.workflow_id).first()

    if not workflow:
        print(f"[API] Workflow not found: {payload.workflow_id}")
        raise HTTPException(status_code=404, detail="Workflow not found")

    if not workflow.is_enabled:
        print(f"[API] Workflow disabled: {workflow.name}")
        raise HTTPException(status_code=400, detail="Workflow is disabled")

    trigger_event = {
        "source": "manual",
        "event": "manual_trigger",
        "config": {
            "title": "Manual Trigger Test",
            "author": "ContentOps",
            "draft_url": "http://127.0.0.1:8000/static/workflows.html",
            "status": "draft",
        },
    }

    run = run_workflow(
        workflow_id=workflow.id,
        trigger_event=trigger_event,
        db=db,
    )

    if not run:
        raise HTTPException(status_code=500, detail="Workflow execution failed")

    print(f"[API] Manual trigger completed | run_id={run.id} | status={run.status}")
    return run