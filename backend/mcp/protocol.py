from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class Tool(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]


class ToolCall(BaseModel):
    name: str
    input: Dict[str, Any]


class ToolResult(BaseModel):
    tool: str
    output: Dict[str, Any]
    error: Optional[str] = None


class RunStep(BaseModel):
    step_index: int
    server: str
    tool: str
    input_map: Dict[str, Any]
    tool_call: Optional[ToolCall] = None
    tool_result: Optional[ToolResult] = None
    error: Optional[str] = None
    status: str = "pending"


class Run(BaseModel):
    id: str
    workflow: str
    trigger: Dict[str, Any]
    steps: List[RunStep]
    status: str = "pending"
    step_outputs: Dict[int, Dict[str, Any]] = Field(default_factory=dict)
    error: Optional[str] = None