import yaml
from typing import Dict, Any
from backend.mcp.server_registry import registry


class WorkflowValidator:
    def __init__(self):
        self.allowed_servers = {
            "notion-mcp",
            "wordpress-mcp",
            "resend-mcp",
            "slack-mcp",
            "qa-gate",
            "qa_gate",
        }

    async def validate_workflow(self, workflow_dict: Dict[str, Any]) -> bool:
        if "workflow" not in workflow_dict:
            raise ValueError("Missing 'workflow' field")
        if "trigger" not in workflow_dict:
            raise ValueError("Missing 'trigger' field")
        if "steps" not in workflow_dict:
            raise ValueError("Missing 'steps' field")

        trigger = workflow_dict["trigger"]
        if trigger.get("server") not in self.allowed_servers:
            raise ValueError(f"Invalid server: {trigger.get('server')}")

        await self._validate_tool(trigger.get("server"), trigger.get("tool"))

        for i, step in enumerate(workflow_dict.get("steps", [])):
            if step.get("server") not in self.allowed_servers:
                raise ValueError(f"Invalid server in step {i}: {step.get('server')}")
            await self._validate_tool(step.get("server"), step.get("tool"))

        return True

    async def _validate_tool(self, server: str, tool_name: str) -> bool:
        try:
            tools = await registry.discover_tools(server)
            tool_names = [tool.name for tool in tools]
            if tool_name not in tool_names:
                raise ValueError(f"Tool {tool_name} not found on {server}. Available: {tool_names}")
            return True
        except Exception as e:
            raise ValueError(f"Failed to validate tool {tool_name} on {server}: {str(e)}")


def load_workflow_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


validator = WorkflowValidator()
