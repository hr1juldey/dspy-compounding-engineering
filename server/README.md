# Compounding Engineering Server

This server implements the Compounding Engineering philosophy using DSPy and FastMCP, enabling both AI agents and humans to collaborate on software development tasks that improve over time.

## Overview

The Compounding Engineering Server is designed to make each unit of engineering work easier than the last by automatically capturing and reapplying knowledge. It provides a unified interface for code review, triage, work execution, planning, and knowledge management.

## Architecture

The server follows a layered architecture:

- **API Layer**: FastAPI endpoints for health, usage, history, and policy checks
- **MCP Layer**: FastMCP server for AI agent interactions
- **Application Layer**: Business logic for commands, queries, and services
- **Domain Layer**: Core entities and value objects
- **Infrastructure Layer**: Persistence, caching, and external service integration
- **Adapters Layer**: Workflow orchestrators and DSPy integration

## How Agents Interact with the Server

### MCP (Model Context Protocol) Integration

AI agents interact with the server through the Model Context Protocol, which provides standardized access to tools and resources:

1. **Tool Access**: Agents can call server-side tools for repository analysis, code review, task execution, etc.
2. **Resource Access**: Agents can retrieve historical data, knowledge base entries, and configuration
3. **Prompt Templates**: Agents can use standardized prompt templates for consistent interactions

### Available MCP Tools

- `run_task`: Execute a general task (review, triage, work, plan, codify)
- `run_review`: Perform multi-agent code review
- `run_triage`: Process code review findings
- `run_work`: Execute work tasks (todo resolution, plan execution)
- `sweep_repository`: Perform comprehensive repository analysis
- `index_repository`: Index repository for knowledge base
- `detect_gaps_in_knowledge`: Identify knowledge gaps
- `update_knowledge_base`: Add new information to knowledge base
- `get_repository_state`: Get current repository state
- `get_task_status`: Check status of a specific task

### DSPy Integration

The server uses DSPy for programming language models rather than prompting them. This allows for:

- Self-improving pipelines that optimize prompts and weights
- Modular AI systems that can be iterated on quickly
- Consistent, high-quality outputs without brittle prompts

## How Humans Interact with the Server

### API Endpoints

Humans can interact with the server through standard API endpoints:

- `GET /health`: Check server health status
- `GET /usage`: Get token usage and task counts
- `GET /history`: Get completed tasks and past sweeps
- `POST /policy`: Decision endpoint for SHOULD_WE_RUN(task, repo)

### CLI Integration

The server is designed to work with the main CLI tool, providing:

- `review`: Multi-agent code review
- `triage`: Interactive findings management
- `work`: Unified todo/plan execution
- `plan`: Feature planning
- `codify`: Explicit learning capture

### Knowledge Management

Humans can contribute to the compounding effect through:

- Explicit feedback via the `codify` command
- Reviewing and approving AI-generated suggestions
- Maintaining the knowledge base with architectural decisions

## Key Features

### 1. Auto-Learning
Every task completion automatically strengthens the system by capturing learnings in the knowledge base.

### 2. KB Auto-Injection
Past learnings automatically inform all AI operations, preventing repeated mistakes.

### 3. Pattern Recognition
The system identifies similar issues and applies past resolutions automatically.

### 4. Knowledge Accumulation
The system gets smarter with every use, making future tasks easier.

## Getting Started

1. **Configuration**: Set up your `.env` file with LLM provider credentials
2. **Start Server**: Run `python -m server.main` to start the FastAPI + FastMCP server
3. **Connect Agents**: Configure AI agents to use the MCP endpoints
4. **Use CLI**: Run `python cli.py` commands to interact with the system

## Security & Privacy

- All sensitive information is scrubbed before being sent to LLMs
- Local-first approach keeps code on your infrastructure
- Authentication can be configured for MCP endpoints
- PII and secrets are automatically detected and redacted

## Contributing

See the main project documentation for contribution guidelines. This server is part of the larger Compounding Engineering ecosystem and follows the same principles of making each contribution easier than the last.