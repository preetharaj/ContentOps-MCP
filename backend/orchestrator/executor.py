import re
import uuid
from typing import Dict, Any, List

from backend.mcp.protocol import ToolCall, RunStep, Run
from backend.mcp.server_registry import registry
from backend.orchestrator.workflow_loader import validator


class WorkflowExecutor:
    def __init__(self, db_connection=None):
        self.db = db_connection
        self.runs = {}

    async def execute_workflow(self, workflow_dict: Dict[str, Any]) -> Run:
        await validator.validate_workflow(workflow_dict)

        run_id = str(uuid.uuid4())

        run = Run(
            id=run_id,
            workflow=workflow_dict.get("workflow"),
            trigger=workflow_dict.get("trigger"),
            steps=[],
        )

        trigger = workflow_dict.get("trigger")
        trigger_server = trigger.get("server")
        trigger_tool = trigger.get("tool")
        trigger_params = trigger.get("params", {})

        try:
            trigger_call = ToolCall(name=trigger_tool, input=trigger_params)
            trigger_result = await registry.call_tool(trigger_server, trigger_call)

            if trigger_result.error:
                run.status = "failed"
                run.error = trigger_result.error
                self.runs[run_id] = run
                return run

            trigger_output = trigger_result.output

        except Exception as e:
            run.status = "failed"
            run.error = str(e)
            self.runs[run_id] = run
            return run

        steps = workflow_dict.get("steps", [])

        for i, step_config in enumerate(steps):
            step = RunStep(
                step_index=i,
                server=step_config.get("server"),
                tool=step_config.get("tool"),
                input_map=step_config.get("input_map", {}),
            )

            try:
                resolved_input = self._resolve_input_map(
                    step_config.get("input_map", {}),
                    trigger_output,
                    run,
                )

                tool_call = ToolCall(name=step.tool, input=resolved_input)
                step.tool_call = tool_call

                tool_result = await registry.call_tool(step.server, tool_call)
                step.tool_result = tool_result

                if tool_result.error:
                    if step.server in {"qa-gate", "qa_gate"} and step.tool == "run_check":
                        step.status = "paused"
                        step.error = tool_result.error
                        run.step_outputs[i] = tool_result.output
                    else:
                        step.status = "failed"
                        step.error = tool_result.error
                else:
                    step.status = "completed"
                    run.step_outputs[i] = tool_result.output

                if step.status in {"failed", "paused"}:
                    run.steps.append(step)
                    break

            except Exception as e:
                step.status = "failed"
                step.error = str(e)

            if step not in run.steps:
                run.steps.append(step)

        if all(s.status == "completed" for s in run.steps):
            run.status = "completed"
        elif any(s.status == "paused" for s in run.steps):
            run.status = "paused"
        elif any(s.status == "failed" for s in run.steps):
            run.status = "failed"
        else:
            run.status = "pending"

        self.runs[run_id] = run
        return run

    def _resolve_input_map(
        self,
        input_map: Dict[str, Any],
        trigger_output: Dict[str, Any],
        run: Run,
    ) -> Dict[str, Any]:
        resolved = {}

        for key, value in input_map.items():
            if isinstance(value, str):
                value = self._resolve_trigger_reference(value, trigger_output)
                value = self._resolve_steps_reference(value, run)

            resolved[key] = value

        return resolved

    def _resolve_path(self, data: Any, path: str) -> Any:
        """
        Supports paths like:
        pages[0].title
        pages[0].body
        url
        slug
        """
        current = data

        parts = path.split(".")

        for part in parts:
            match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)(?:\[(\d+)\])?$", part)

            if not match:
                return None

            key = match.group(1)
            index = match.group(2)

            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None

            if index is not None:
                if isinstance(current, list):
                    idx = int(index)
                    if idx >= len(current):
                        return None
                    current = current[idx]
                else:
                    return None

        return current

    def _resolve_trigger_reference(
        self,
        template: str,
        trigger_output: Dict[str, Any],
    ) -> str:
        def replace_ref(match):
            full_match = match.group(0)
            path = match.group(1)

            value = self._resolve_path(trigger_output, path)

            if value is None:
                return full_match

            return str(value)

        return re.sub(r"\{trigger\.([^}]+)\}", replace_ref, template)

    def _resolve_steps_reference(self, template: str, run: Run) -> str:
        def replace_ref(match):
            full_match = match.group(0)
            step_index = int(match.group(1))
            path = match.group(2)

            if step_index not in run.step_outputs:
                return full_match

            value = self._resolve_path(run.step_outputs[step_index], path)

            if value is None:
                return full_match

            return str(value)

        return re.sub(r"\{steps\[(\d+)\]\.([^}]+)\}", replace_ref, template)

    def get_run(self, run_id: str) -> Run:
        return self.runs.get(run_id)

    def list_runs(self) -> List[Run]:
        return list(self.runs.values())


executor = WorkflowExecutor()