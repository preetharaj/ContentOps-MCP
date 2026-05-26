from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI()

TOOLS = [
    {
        "name": "create_draft",
        "description": "Create a draft post on WordPress.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["title"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "slug": {"type": "string"},
                "url": {"type": "string"}
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
    if call.name != "create_draft":
        raise HTTPException(status_code=400, detail=f"Tool {call.name} not found")
    
    title = call.input.get("title")
    if not title:
        raise HTTPException(status_code=400, detail="Missing title")
    
    slug = title.lower().replace(" ", "-")
    return {
        "tool": call.name,
        "output": {
            "slug": slug,
            "url": f"https://example.com/draft/{slug}"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)
