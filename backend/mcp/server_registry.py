import re
from typing import Any, Dict, List

import httpx

from backend.mcp.protocol import Tool, ToolCall, ToolResult
from backend.orchestrator.qa_gate import run_qa_gate


class ServerRegistry:
    def __init__(self):
        self.servers = {
            "notion-mcp": "http://127.0.0.1:8001",
            "wordpress-mcp": "http://127.0.0.1:8002",
            "resend-mcp": "http://127.0.0.1:8003",
            "slack-mcp": "http://127.0.0.1:8004",
            "qa-gate": "local://qa-gate",
            "qa_gate": "local://qa-gate",
        }
        self.tools_cache: Dict[str, List[Tool]] = {}
        self.local_tools = self._build_local_tools()

    def _build_local_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        any_object = {"type": "object", "additionalProperties": True}
        return {
            "notion-mcp": [
                {
                    "name": "get_pages",
                    "description": "Get editorial pages from a Notion database.",
                    "input_schema": any_object,
                    "output_schema": any_object,
                },
                {"name": "get_page", "description": "Get one Notion page.", "input_schema": any_object, "output_schema": any_object},
            ],
            "wordpress-mcp": [
                {"name": "create_draft", "description": "Create a WordPress draft.", "input_schema": any_object, "output_schema": any_object},
                {"name": "get_page", "description": "Fetch a WordPress draft/page.", "input_schema": any_object, "output_schema": any_object},
                {"name": "get_links", "description": "Extract links from a WordPress page or content body.", "input_schema": any_object, "output_schema": any_object},
                {"name": "publish_post", "description": "Publish a WordPress post after QA approval.", "input_schema": any_object, "output_schema": any_object},
            ],
            "resend-mcp": [
                {"name": "send_email", "description": "Send email through Resend.", "input_schema": any_object, "output_schema": any_object},
            ],
            "slack-mcp": [
                {"name": "post_message", "description": "Post a Slack message.", "input_schema": any_object, "output_schema": any_object},
            ],
            "qa-gate": [
                {"name": "run_check", "description": "Run draft-to-publish QA gate.", "input_schema": any_object, "output_schema": any_object},
                {"name": "override_and_publish", "description": "Override QA result and continue publishing.", "input_schema": any_object, "output_schema": any_object},
                {"name": "retry_after_edit", "description": "Retry QA gate after the editor updates the draft.", "input_schema": any_object, "output_schema": any_object},
                {"name": "send_to_editor_channel", "description": "Send QA result to an editor channel.", "input_schema": any_object, "output_schema": any_object},
            ],
            "qa_gate": [
                {"name": "run_check", "description": "Run draft-to-publish QA gate.", "input_schema": any_object, "output_schema": any_object},
            ],
        }

    async def discover_tools(self, server_name: str) -> List[Tool]:
        if server_name in self.tools_cache:
            return self.tools_cache[server_name]

        url = self.servers.get(server_name)
        if not url:
            raise ValueError(f"Server {server_name} not found")

        if url.startswith("local://"):
            return self._local_tool_models(server_name)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{url}/tools", timeout=2.0)
                response.raise_for_status()
                tools_data = response.json().get("tools", [])
                tools = [Tool(**tool) for tool in tools_data]
                self.tools_cache[server_name] = tools
                return tools
        except Exception:
            return self._local_tool_models(server_name)

    async def call_tool(self, server_name: str, tool_call: ToolCall) -> ToolResult:
        url = self.servers.get(server_name)
        if not url:
            return ToolResult(tool=tool_call.name, output={}, error=f"Server {server_name} not found")

        if url.startswith("local://"):
            return await self._call_local_tool(server_name, tool_call)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{url}/use_tool", json=tool_call.dict(), timeout=5.0)
                response.raise_for_status()
                result_data = response.json()
                return ToolResult(tool=result_data.get("tool", tool_call.name), output=result_data.get("output", {}))
        except httpx.HTTPStatusError as e:
            try:
                error_msg = e.response.json().get("detail", str(e))
            except Exception:
                error_msg = str(e)
            return ToolResult(tool=tool_call.name, output={}, error=error_msg)
        except Exception:
            return await self._call_local_tool(server_name, tool_call)

    def _local_tool_models(self, server_name: str) -> List[Tool]:
        tools = [Tool(**tool) for tool in self.local_tools.get(server_name, [])]
        self.tools_cache[server_name] = tools
        return tools

    async def _call_local_tool(self, server_name: str, tool_call: ToolCall) -> ToolResult:
        data = tool_call.input or {}
        name = tool_call.name

        if server_name == "notion-mcp" and name in {"get_pages", "get_page"}:
            page = {
                "id": "notion-page-demo",
                "title": data.get("title") or "MCP-native ContentOps: QA before publishing",
                "body": data.get("content") or (
                    "# MCP-native ContentOps\n\n"
                    "This practical guide explains how a content team can create a WordPress draft, "
                    "run a QA gate, check links, verify brand voice, and publish only after approval. "
                    "Example: a Notion page becomes a draft, QA pauses risky posts, and editors can override when needed."
                ),
                "meta_description": "A practical guide to MCP-native draft QA before content publishing.",
            }
            return ToolResult(tool=name, output={"pages": [page], "page": page})

        if server_name == "wordpress-mcp" and name == "create_draft":
            title = data.get("title") or "Untitled Draft"
            slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "untitled-draft"
            return ToolResult(tool=name, output={"post_id": "wp-demo-1", "slug": slug, "url": f"http://localhost:8000/drafts/{slug}", "status": "draft"})

        if server_name == "wordpress-mcp" and name == "get_page":
            content = data.get("content") or "Demo draft content with an internal link to /static/workflows.html."
            return ToolResult(tool=name, output={"title": data.get("title", "Demo draft"), "content": content, "links": ["/static/workflows.html"]})

        if server_name == "wordpress-mcp" and name == "get_links":
            links = re.findall(r"\[[^\]]+\]\(([^)]+)\)|href=[\"']([^\"']+)[\"']", data.get("content", ""))
            flattened = [a or b for a, b in links]
            return ToolResult(tool=name, output={"links": flattened})

        if server_name == "wordpress-mcp" and name == "publish_post":
            if str(data.get("qa_passed", "true")).lower() in {"false", "0", "no"}:
                return ToolResult(tool=name, output={}, error="QA gate did not pass; publish_post halted.")
            return ToolResult(tool=name, output={"status": "published", "url": data.get("url") or "http://localhost:8000/demo-post"})

        if server_name == "resend-mcp" and name == "send_email":
            return ToolResult(tool=name, output={"id": "email-demo-1", "status": "sent", "to": data.get("to", "team@example.com")})

        if server_name == "slack-mcp" and name == "post_message":
            return ToolResult(tool=name, output={"ok": True, "channel": data.get("channel", "#content-team"), "text": data.get("text", "")})

        if server_name in {"qa-gate", "qa_gate"} and name in {"run_check", "retry_after_edit", "send_to_editor_channel"}:
            if name == "send_to_editor_channel":
                data = {**data, "mode": "send_to_editor"}
            result = await run_qa_gate(data)
            return ToolResult(tool=name, output=result, error=None if result.get("pass") else result.get("reasoning"))

        if server_name in {"qa-gate", "qa_gate"} and name == "override_and_publish":
            result = await run_qa_gate({**data, "override": True, "mode": "auto_publish"})
            return ToolResult(tool=name, output=result)

        return ToolResult(tool=name, output={}, error=f"Local fallback for {server_name}::{name} not implemented")


registry = ServerRegistry()
