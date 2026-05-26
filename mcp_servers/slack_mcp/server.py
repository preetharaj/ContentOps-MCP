from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI()

TOOLS = [
    {
        "name": "post_message",
        "description": "Post a message to a Slack channel.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel": {"type": "string"},
                "text": {"type": "string"}
            },
            "required": ["channel", "text"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "ok": {"type": "boolean"},
                "ts": {"type": "string"}
            }
        }
    }
]

class ToolCall(BaseModel):
    name: str
    input: Dict[str, Any]

@app.get("/tools")
def get_tools():
    return {"tools": TOOLS}

@app.post("/use_tool")
def use_tool(call: ToolCall):
    if call.name != "post_message":
        raise HTTPException(status_code=400, detail=f"Tool {call.name} not found")
    
    channel = call.input.get("channel")
    text = call.input.get("text")
    if not channel or not text:
        raise HTTPException(status_code=400, detail="Missing channel or text")
    
    return {
        "tool": call.name,
        "output": {
            "ok": True,
            "ts": "1234567890.123456"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8004)
