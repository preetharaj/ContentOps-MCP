"""
Content-ops Orchestrator - FastAPI Backend
Main entry point for Day 3 setup.
"""

from dotenv import load_dotenv
# Load environment variables
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager


from backend.database import Base, engine
from backend.web.api import router as api_router
from backend.engine.scheduler import start_scheduler, stop_scheduler
from backend.orchestrator.executor import executor
from backend.mcp.protocol import Run

# Create database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app startup and shutdown events."""
    # Startup
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()

app = FastAPI(
    title="Content-ops Orchestrator",
    description="MCP-inspired workflow orchestrator: Notion → blog → Slack → email",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router
app.include_router(api_router)

# MCP Orchestrator Routes
@app.post("/mcp/workflows/execute")
async def execute_workflow(workflow: dict):
    """Execute a workflow and return the run."""
    run = await executor.execute_workflow(workflow)
    return run.dict()

@app.get("/mcp/resources/runs/{run_id}")
def get_run(run_id: str):
    """Get a run by ID (MCP resource)."""
    run = executor.get_run(run_id)
    if not run:
        return {"error": "Run not found"}, 404
    return run.dict()

@app.get("/mcp/resources/runs/{run_id}/trace")
def get_run_trace(run_id: str):
    """Get a run's trace (steps and results)."""
    run = executor.get_run(run_id)
    if not run:
        return {"error": "Run not found"}, 404
    
    trace = {
        "run_id": run.id,
        "workflow": run.workflow,
        "status": run.status,
        "steps": []
    }
    
    for step in run.steps:
        trace["steps"].append({
            "step_index": step.step_index,
            "server": step.server,
            "tool": step.tool,
            "status": step.status,
            "tool_call": step.tool_call.dict() if step.tool_call else None,
            "tool_result": step.tool_result.dict() if step.tool_result else None,
            "error": step.error
        })
    
    return trace

@app.get("/mcp/resources/runs")
def list_runs():
    """List all runs."""
    runs = executor.list_runs()
    return [run.dict() for run in runs]


@app.get("/workflows")
def workflows_page():
    """Serve the workflow list UI at a clean route."""
    return FileResponse("static/workflows.html")

@app.get("/workflows/qa-gate-demo")
def qa_gate_demo_page():
    """Serve the Phase 3 QA-gate demo UI at a clean route."""
    return FileResponse("static/workflows.html")

@app.get("/runs")
def runs_page():
    """Serve the runs UI at a clean route."""
    return FileResponse("static/runs.html")

# Mount frontend static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/registry", StaticFiles(directory="registry", html=True), name="registry")

@app.get("/")
def read_root():
    """Serve the static UI home page."""
    return FileResponse("static/index.html")

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Content-ops Orchestrator API running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)