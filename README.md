# Agentic Todo Assistant

An AI agent built with FastAPI and Google Gemini that manages todos from plain-language instructions. Instead of calling endpoints manually, you type something like "Add 3 todos for exam prep" and the agent decides which actions to take.

## Features
- Natural language control of todos (create, complete, delete, list)
- Gemini function calling with automatic tool selection
- Simple web UI at `/` (no Postman needed)
- REST endpoints with auto-generated Swagger docs at `/docs`

## Tech Stack
Python, FastAPI, Google Gemini API (function calling), Uvicorn, HTML/CSS/JS

## How It Works
1. Todo operations are plain Python functions (`create_todo`, `delete_todo`, `mark_complete`, `list_todos`).
2. These are passed to Gemini as tools. Gemini reads the docstrings and type hints to understand each one.
3. With automatic function calling enabled, Gemini decides which tool to call and when, runs it, and returns a final response.

## Setup
```bash
git clone https://github.com/rudrakrishna13062004-cmyk/<repo-name>
cd <repo-name>
pip install -r requirements.txt
export GEMINI_API_KEY="your_key_here"
python main.py
```
Get a free API key from [Google AI Studio](https://aistudio.google.com). Then open `http://localhost:8000`.

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ai/agent` | Send an instruction to the agent |
| GET | `/todos` | List all todos |
| GET | `/` | Web UI |

## Example
Instruction: `Add 3 todos for exam prep and mark the first as high priority`

## Limitations
- Todos are stored in memory and reset when the server restarts.
- No authentication yet.

## Future Improvements
- Persistent storage (SQLite) and JWT auth
- Update/edit todo tool
- Deploy on Render

## Author
Kishan Kumar | BCA Student | Python Backend & AI
[GitHub](https://github.com/rudrakrishna13062004-cmyk) | [LinkedIn](https://www.linkedin.com/in/kishan-kumar-b8019939b)
