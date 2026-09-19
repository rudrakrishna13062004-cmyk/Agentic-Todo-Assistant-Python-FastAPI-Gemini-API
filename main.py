"""
Agentic Todo Assistant - FastAPI + Google Gemini (function calling)

Ek natural language instruction se agent khud decide karta hai ki
todo create / complete / delete / list karna hai.

SETUP:
1. pip install -r requirements.txt
2. Same folder mein .env file banao:   GEMINI_API_KEY=your_key_here
   (key: aistudio.google.com/api-keys). .env ko GitHub par push mat karo.
3. python main.py   ->   http://localhost:8000
"""

import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

API_KEY = ("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY set nahi hai. .env file ya environment variable mein daalo."
    )

MODEL_NAME = "gemini-3.1-flash-lite"
client = genai.Client(api_key=API_KEY)
app = FastAPI(title="Agentic Todo Assistant")

# -------------------------------------------------------------------
# In-memory storage (server restart par reset ho jata hai)
# -------------------------------------------------------------------
todos = {}
next_id = 1
VALID_PRIORITIES = {"low", "medium", "high"}


# -------------------------------------------------------------------
# Tools: normal Python functions. Gemini docstring + type hints se
# samajhta hai ki inka kaam kya hai.
# -------------------------------------------------------------------
def create_todo(title: str, priority: str = "medium") -> dict:
    """Create a new todo item with a title and priority (low, medium, or high)."""
    global next_id
    priority = priority.lower().strip()
    if priority not in VALID_PRIORITIES:
        priority = "medium"
    todo = {"id": next_id, "title": title, "priority": priority, "completed": False}
    todos[next_id] = todo
    next_id += 1
    return todo


def delete_todo(todo_id: int) -> dict:
    """Delete a todo item using its ID number."""
    todo_id = int(todo_id)
    if todo_id in todos:
        return {"status": "deleted", "todo": todos.pop(todo_id)}
    return {"status": "not_found"}


def mark_complete(todo_id: int) -> dict:
    """Mark a todo item as completed using its ID number."""
    todo_id = int(todo_id)
    if todo_id in todos:
        todos[todo_id]["completed"] = True
        return todos[todo_id]
    return {"status": "not_found"}


def list_todos() -> dict:
    """Get the current list of all todo items."""
    return {"todos": list(todos.values())}


TOOLS = [create_todo, delete_todo, mark_complete, list_todos]

SYSTEM_INSTRUCTION = (
    "You are a todo assistant. Use the provided tools to create, complete, "
    "delete or list todos. If the user asks for a plan, create multiple todos. "
    "Reply briefly, in the same language as the user."
)


# -------------------------------------------------------------------
# Agent endpoint. Python functions ko tools ki tarah dene par SDK
# automatic function calling karta hai: model tool chunta hai, SDK
# usse chalata hai, aur final jawab wapas aata hai.
# -------------------------------------------------------------------
class AgentRequest(BaseModel):
    instruction: str = Field(min_length=1, max_length=500)


@app.post("/ai/agent")
def run_agent(request: AgentRequest):
    instruction = request.instruction.strip()
    if not instruction:
        raise HTTPException(status_code=400, detail="Instruction khali hai.")

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=instruction,
            config=types.GenerateContentConfig(
                tools=TOOLS,
                system_instruction=SYSTEM_INSTRUCTION,
            ),
        )
        result = response.text or "Done."
    except Exception as e:
        print("Gemini error:", e)
        raise HTTPException(
            status_code=502,
            detail="AI se response nahi mila. Thodi der baad dobara try karo.",
        )

    return {"result": result, "current_todos": list(todos.values())}


@app.get("/todos")
def get_all_todos():
    return list(todos.values())


# -------------------------------------------------------------------
# Simple UI: browser mein "/" kholo, Postman ki zaroorat nahi
# -------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home_page():
    return """
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Agentic Todo Assistant</title>
        <style>
            body { font-family: sans-serif; background: #111; color: #eee; padding: 20px; }
            input { width: 65%; padding: 10px; font-size: 16px; }
            button { padding: 10px 20px; font-size: 16px; background: #4a90d9; color: white; border: none; }
            button:disabled { opacity: 0.6; }
            #todos { margin-top: 20px; }
            .todo { padding: 8px; margin: 5px 0; background: #222; border-left: 4px solid #4a90d9; }
            .high { border-left-color: #e74c3c; }
            .medium { border-left-color: #f39c12; }
            .low { border-left-color: #2ecc71; }
            #result { margin-top: 15px; color: #9fd; }
        </style>
    </head>
    <body>
        <h2>Agentic Todo Assistant</h2>
        <p>Ek instruction likho, jaise: "Add 3 todos for exam prep"</p>
        <input id="instruction" type="text" placeholder="Apna instruction yaha likho..." />
        <button id="sendBtn" onclick="sendInstruction()">Send</button>
        <p id="result"></p>
        <div id="todos"></div>

        <script>
            const input = document.getElementById("instruction");
            const btn = document.getElementById("sendBtn");
            const resultEl = document.getElementById("result");

            input.addEventListener("keydown", (e) => {
                if (e.key === "Enter") sendInstruction();
            });

            async function sendInstruction() {
                const text = input.value.trim();
                if (!text) return;
                btn.disabled = true;
                resultEl.innerText = "Soch raha hai...";
                try {
                    const res = await fetch("/ai/agent", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ instruction: text })
                    });
                    const data = await res.json();
                    if (!res.ok) {
                        resultEl.innerText = "Error: " + (data.detail || "kuch galat hua");
                    } else {
                        resultEl.innerText = data.result;
                        renderTodos(data.current_todos);
                        input.value = "";
                    }
                } catch (err) {
                    resultEl.innerText = "Server se connect nahi ho paya.";
                }
                btn.disabled = false;
            }

            function renderTodos(list) {
                const container = document.getElementById("todos");
                container.innerHTML = "<h3>Current Todos:</h3>";
                list.forEach(t => {
                    const div = document.createElement("div");
                    div.className = "todo " + t.priority;
                    div.innerText = (t.completed ? "[done] " : "[ ] ") + t.title + " (" + t.priority + ")";
                    container.appendChild(div);
                });
            }

            fetch("/todos").then(r => r.json()).then(renderTodos);
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
