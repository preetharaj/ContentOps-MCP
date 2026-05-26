"""
Workflow runner: executes a workflow and its steps.
"""

import logging
import asyncio
import importlib
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models.workflow import Workflow
from backend.models.run import Run
from backend.models.step import Step
from backend.models.run_step import RunStep

logger = logging.getLogger(__name__)


async def execute_step(
    step: Step,
    trigger_event: Dict[str, Any],
    previous_outputs: Dict[int, Dict[str, Any]]
) -> Dict[str, Any]:

    try:
        print("-" * 80)
        print(f"[RUNNER] Preparing step {step.id}: {step.app}.{step.action}")

        module_name = f"backend.steps.{step.app}"
        print(f"[RUNNER] Importing module: {module_name}")

        module = importlib.import_module(module_name)

        action_func = getattr(module, step.action, None)
        if not action_func:
            raise ValueError(f"Action '{step.action}' not found in module '{module_name}'")

        func_params = {**(step.parameters or {})}

        if "config" in trigger_event:
            func_params.update(trigger_event["config"])

        for prev_step_id, prev_output in previous_outputs.items():
            if isinstance(prev_output, dict) and prev_output.get("status") == "success":
                func_params.update(prev_output)

        safe_params = {
            key: value
            for key, value in func_params.items()
            if "key" not in key.lower()
            and "token" not in key.lower()
            and "secret" not in key.lower()
        }

        print(f"[RUNNER] Calling {step.app}.{step.action}")
        print(f"[RUNNER] Params: {safe_params}")

        result = await action_func(**func_params)

        print(f"[RUNNER] Step {step.id} result: {result}")
        return result

    except Exception as e:
        error_msg = f"Error executing step {step.id} ({step.app}.{step.action}): {str(e)}"
        print(f"[RUNNER] {error_msg}")
        logger.error(error_msg)

        return {
            "status": "error",
            "error": str(e),
        }


def run_workflow(
    workflow_id: int,
    trigger_event: Dict[str, Any],
    db: Optional[Session] = None
) -> Optional[Run]:

    return asyncio.run(_run_workflow_async(workflow_id, trigger_event, db))


async def _run_workflow_async(
    workflow_id: int,
    trigger_event: Dict[str, Any],
    db: Optional[Session] = None
) -> Optional[Run]:

    if db is None:
        db = SessionLocal()
        own_session = True
    else:
        own_session = False

    try:
        print("=" * 80)
        print(f"[RUNNER] Starting workflow execution | workflow_id={workflow_id}")
        print(f"[RUNNER] Trigger event: {trigger_event}")
        print("=" * 80)

        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()

        if not workflow:
            print(f"[RUNNER] Workflow {workflow_id} not found")
            return None

        if not workflow.is_enabled:
            print(f"[RUNNER] Workflow {workflow_id} is disabled")
            return None

        print(f"[RUNNER] Workflow found: {workflow.name}")

        run = Run(
            workflow_id=workflow_id,
            status="running",
            started_at=datetime.utcnow(),
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        print(f"[RUNNER] Created run_id={run.id}")

        steps = (
            db.query(Step)
            .filter(Step.workflow_id == workflow_id)
            .order_by(Step.id)
            .all()
        )

        print(f"[RUNNER] Found {len(steps)} step(s)")

        run_steps_map = {}

        for step in steps:
            print(f"[RUNNER] Registering step {step.id}: {step.app}.{step.action}")

            run_step = RunStep(
                run_id=run.id,
                step_id=step.id,
                status="pending",
            )
            db.add(run_step)
            run_steps_map[step.id] = run_step

        db.commit()

        previous_outputs = {}
        workflow_failed = False

        for step in steps:
            run_step = run_steps_map[step.id]

            print("-" * 80)
            print(f"[RUNNER] Starting step {step.id}: {step.app}.{step.action}")

            run_step.status = "running"
            db.commit()

            result = await execute_step(step, trigger_event, previous_outputs)

            if result.get("status") == "error":
                run_step.status = "failed"
                run_step.error = result.get("error", "Unknown error")
                run_step.output = result
                db.commit()

                print(f"[RUNNER] Step {step.id} FAILED")
                print(f"[RUNNER] Error: {run_step.error}")
                print("[RUNNER] Workflow halted")

                workflow_failed = True
                break

            run_step.status = "completed"
            run_step.output = result
            db.commit()

            print(f"[RUNNER] Step {step.id} completed successfully")

            previous_outputs[step.id] = result

        run.ended_at = datetime.utcnow()

        if workflow_failed:
            run.status = "failed"
            print(f"[RUNNER] Run {run.id} FAILED")
        else:
            run.status = "completed"
            print(f"[RUNNER] Run {run.id} COMPLETED SUCCESSFULLY")

        db.commit()
        db.refresh(run)

        print("=" * 80)
        print(f"[RUNNER] Finished workflow | run_id={run.id} | status={run.status}")
        print("=" * 80)

        return run

    except Exception as e:
        print(f"[RUNNER] Unexpected error running workflow {workflow_id}: {e}")
        logger.error(f"Unexpected error running workflow {workflow_id}: {e}")
        return None

    finally:
        if own_session:
            db.close()