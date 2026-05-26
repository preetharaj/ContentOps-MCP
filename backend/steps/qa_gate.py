"""Legacy workflow-step wrapper for the Phase 3 QA gate."""

from typing import Any, Dict

from backend.orchestrator.qa_gate import run_qa_gate


async def run_check(**kwargs: Any) -> Dict[str, Any]:
    result = await run_qa_gate(kwargs)
    if result.get("pass"):
        return {"status": "success", **result}
    return {"status": "error", "error": result.get("reasoning", "QA gate failed"), **result}


async def override_and_publish(**kwargs: Any) -> Dict[str, Any]:
    kwargs["override"] = True
    kwargs["mode"] = "auto_publish"
    result = await run_qa_gate(kwargs)
    return {"status": "success", **result}


async def retry_after_edit(**kwargs: Any) -> Dict[str, Any]:
    return await run_check(**kwargs)


async def send_to_editor_channel(**kwargs: Any) -> Dict[str, Any]:
    kwargs["mode"] = "send_to_editor"
    result = await run_qa_gate(kwargs)
    return {"status": "success", "sent_to_editor": True, **result}
