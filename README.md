# TaskFlow — AI Task Manager

TaskFlow is an AI-powered task management application that lets users create, view, update, and delete tasks using natural-language instructions.

## Features

- AI-powered task management
- Create, search, update, and delete tasks
- Web-based task board
- Context-aware AI conversations
- Conversation history
- Confirmation before task deletion

## Tech Stack

- Python
- FastAPI
- LangGraph
- LangChain
- SQLAlchemy
- SQLite
- HTML, CSS, JavaScript
- uv
- Groq API

## Project Structure

```text
TaskFlow/
├── app/
│   ├── llm.py
│   ├── task_service.py
│   └── ...
├── static/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Fail2/TaskFlow.git
cd TaskFlow
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Configure Environment Variables

Create a `.env` file by copying `.env.example`:

```bash
cp .env.example .env
```


Open `.env` and replace `Your Api Key` with your [Groq API key](https://console.groq.com/keys).

```env
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=your_groq_api_key
LLM_MODEL=openai/gpt-oss-120b
```

Keep your API key private. Never commit `.env` to GitHub.

### 4. Run the Application

```bash
uv run uvicorn app.main:app --reload
```

Adjust the command if your FastAPI entry point differs from `app.main:app`.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/tasks` | Retrieve tasks |
| POST | `/chat` | Send a message to the AI assistant |
| GET | `/history` | Retrieve conversation history |

## AI Workflow

TaskFlow uses LangGraph to process user instructions and execute task-management tools.

- `create_tasks` — Create tasks.
- `list_tasks` — Retrieve or search tasks.
- `update_task` — Update task details.
- `delete_task` — Delete tasks after explicit confirmation.

The assistant identifies the intended task and asks for clarification when necessary.

## Conversation History

TaskFlow uses thread-based conversation state management with LangGraph checkpointing.

The frontend stores the conversation thread ID in browser `localStorage` using the key `taskflow_thread_id`. The `/history` endpoint retrieves conversation history.

## Example Commands

Users can manage tasks using natural-language instructions:

- `Create a high-priority task to finish the demo tomorrow.`
- `Show all tasks.`
- `Show unfinished tasks related to documentation.`
- `Move TSK-0001 to In progress.`
- `Update the priority of the selected task to high.`
- `Delete the selected task.`

The assistant may ask follow-up questions or request confirmation when needed.

## License

No license specified yet.
