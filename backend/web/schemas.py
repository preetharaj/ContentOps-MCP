"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class TriggerSchema(BaseModel):
    app: str
    event: str
    config: Dict[str, Any] = {}

    class Config:
        from_attributes = True

class StepSchema(BaseModel):
    id: Optional[int] = None
    workflow_id: Optional[int] = None
    app: str
    action: str
    parameters: Dict[str, Any] = {}

    class Config:
        from_attributes = True

class WorkflowCreateSchema(BaseModel):
    name: str
    is_enabled: bool = True
    trigger: TriggerSchema
    steps: List[StepSchema] = []

class WorkflowSchema(BaseModel):
    id: int
    name: str
    is_enabled: bool
    trigger: Dict[str, Any]
    steps: List[StepSchema] = []

    class Config:
        from_attributes = True

class RunStepSchema(BaseModel):
    id: int
    run_id: int
    step_id: int
    status: str
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True

class RunSchema(BaseModel):
    id: int
    workflow_id: int
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    run_steps: List[RunStepSchema] = []

    class Config:
        from_attributes = True

class TriggerWorkflowSchema(BaseModel):
    workflow_id: int
    trigger_data: Dict[str, Any] = {}
