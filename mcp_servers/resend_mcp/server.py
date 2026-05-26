from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI()

TOOLS = [
    {
        "name": "send_email",
        "description": "Send an email via Resend.",
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": {"type": "string"},
                "body": {"type": "string"},
                "to": {"type": "string"},
                "from": {"type": "string"}
            },
            "required": ["subject", "body"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "status": {"type": "string"}
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
    if call.name != "send_email":
        raise HTTPException(status_code=400, detail=f"Tool {call.name} not found")
    
    subject = call.input.get("subject")
    body = call.input.get("body")
    if not subject or not body:
        raise HTTPException(status_code=400, detail="Missing subject or body")
    
    return {
        "tool": call.name,
        "output": {
            "id": "email-123456",
            "status": "sent"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8003)
