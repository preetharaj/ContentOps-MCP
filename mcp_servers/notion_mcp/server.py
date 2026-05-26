from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

app = FastAPI()

TOOLS = [
    {
        "name": "get_pages",
        "description": "Get pages from a Notion database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "database_id": {"type": "string"}
            },
            "required": ["database_id"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "pages": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "title": {"type": "string"},
                            "body": {"type": "string"}
                        }
                    }
                }
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
    if call.name != "get_pages":
        raise HTTPException(status_code=400, detail=f"Tool {call.name} not found")
    
    database_id = call.input.get("database_id")
    if not database_id:
        raise HTTPException(status_code=400, detail="Missing database_id")
    
    return {
        "tool": call.name,
        "output": {
            "pages": [
                {
                    "id": "page-1",
                    "title": "Editorial Calendar Page",
                    "body": "Content for the editorial calendar page."
                }
            ]
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
