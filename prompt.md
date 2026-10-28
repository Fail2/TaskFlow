# TaskFlow — AI-Assisted Development Prompts

## 1. Project Planning

**Prompt 1 — Creating PROJECT.md with Claude**
> I want to build an AI-powered task management application. Help me prepare a `PROJECT.md` file describing the project requirements, features, tech stack, and development plan so I can follow it step by step.Here I attach files about requirements.

**Prompt 2 — Getting Started with Gemini**
> I have prepared my `PROJECT.md` with Claude's help. Based on this project plan, guide me on how to initialize the project. Give me the required terminal commands one by one and explain where and how to run them. I want to build the project step by step.



## 2. Backend Development

**Prompt 3 — Building the Backend**
> Help me build the backend first using FastAPI, SQLite, LangGraph, and an LLM API. Let's implement the task management tools and chat functionality step by step without building the frontend yet.

**Prompt 4 — Testing APIs**
> My backend is ready. How can I test all the APIs? Guide me step by step on which endpoints to test, what request data to provide, and how to check whether each API is working correctly. I'll test them one by one and share the responses if I encounter any errors.

**Prompt 5 — Debugging API Responses**
> I tested the endpoint and got this response/error: [insert response or error]. Help me understand the problem and fix it before I move to the next endpoint.

## 3. AI Workflow and History

**Prompt 6 — Testing Task Tools**
> Help me test whether the AI can create, list, update, and delete tasks correctly. Also verify that it asks for confirmation before deleting a task.

**Prompt 7 — Conversation History**
> Help me test whether the chat remembers previous messages and whether `/history` returns the correct conversation. If something doesn't work, let's debug it using the actual API responses.

## 4. Frontend Development

**Prompt 8 — Building the Frontend**
> Now that the backend and API testing are done, help me build the frontend using HTML, CSS, and JavaScript. Use my UI reference for the design, keep the existing project structure, and connect the frontend to the backend APIs.

**Prompt 9 — Final Integration**
> Help me test the complete application from the frontend. Check task operations, AI chat, conversation history, error handling, and responsive layout. Fix any issues we find one by one.

## Development Process

1. Created `PROJECT.md` with Claude's help.
2. Got the initial setup command from Gemini.
3. Developed the backend before starting the frontend.
4. Tested endpoints individually through FastAPI Swagger UI (`/docs`).
5. Used API responses and errors to debug the AI workflow.
6. Built the frontend and connected it to the backend.
7. Tested the complete application and fixed integration issues.