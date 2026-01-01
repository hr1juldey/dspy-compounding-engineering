# Compounding Engineering MCP+API Server

## Overview

Production-grade **FastMCP + FastAPI + Celery** server that exposes all CLI functionality via:

- **HTTP REST API** - For web clients and integrations
- **WebSocket** - Real-time progress streaming
- **MCP Protocol** (stdio) - For AI clients (Claude Desktop, Cursor)

**Multi-Repo Support**: Each repo maintains its own `.compounding/` directory.

---

## Quick Start

### 1. Start Infrastructure

```bash
# Start Redis and Qdrant
docker compose up redis qdrant -d
```

### 2. Start Server (Development)

```bash
# Terminal 1: Start Celery Worker
celery -A server.infrastructure.celery.app worker --loglevel=info

# Terminal 2: Start FastAPI Server
uvicorn server.main:app --host 127.0.0.1 --port 12000 --reload
```

### 3. Start Server (Production)

```bash
# Start all services via Docker Compose
docker compose up server celery-worker -d

# View logs
docker compose logs -f server celery-worker
```

---

## Usage Examples

### HTTP API

```bash
# Submit analysis task
curl -X POST http://localhost:12000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repo_root": "/path/to/repo",
    "entity": "MyClass",
    "analysis_type": "navigate"
  }'

# Returns: {"task_id": "abc123..."}

# Get task status
curl http://localhost:12000/api/v1/analyze/abc123

# Check server health
curl http://localhost:12000/health
```

### WebSocket (Real-time Progress)

```javascript
const ws = new WebSocket('ws://localhost:12000/ws/task/' + taskId);

ws.onmessage = (event) => {
  const progress = JSON.parse(event.data);
  console.log(`${progress.percent}%: ${progress.message}`);
};
```

### MCP Client (Claude Desktop)

Add to `~/.config/claude/config.json`:

```json
{
  "mcpServers": {
    "compounding-engineering": {
      "command": "python",
      "args": ["-m", "server.mcp.server"],
      "cwd": "/path/to/dspy-compounding-engineering"
    }
  }
}
```

Then use MCP tools in Claude Desktop:

- `analyze_code` - Code analysis
- `execute_work` - Execute todos/plans
- `review_code` - Code review
- `garden_knowledge` - KB maintenance
- `generate_plan` - Plan generation
- `check_policies` - Policy enforcement
- `get_task_status` - Check task status
- `initialize_repo` - Create .compounding/ for new repo

---

## Available Endpoints

### FastAPI HTTP Endpoints

- `POST /api/v1/analyze` - Submit analysis
- `GET /api/v1/analyze/{task_id}` - Get analysis status
- `POST /api/v1/work` - Execute work items
- `GET /api/v1/work/{task_id}` - Get work status
- `POST /api/v1/review` - Submit code review
- `GET /api/v1/review/{task_id}` - Get review status
- `POST /api/v1/garden` - Submit gardening
- `GET /api/v1/garden/{task_id}` - Get garden status
- `POST /api/v1/plan` - Generate plan
- `GET /api/v1/plan/{task_id}` - Get plan status
- `POST /api/v1/check` - Check policies (synchronous)
- `GET /api/v1/config` - Configuration UI
- `POST /api/v1/config` - Update .env
- `WS /ws/task/{task_id}` - Progress stream
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /docs` - OpenAPI docs

### MCP Tools

All MCP tools follow hybrid behavior:

- **Long operations** (analyze, work, review, garden, plan): Return `task_id` immediately
- **Fast operations** (check_policies, get_repo_status): Block and return result

Use `get_task_status(task_id)` to poll long operations.

---

## Multi-Repo Workflow

The server supports multiple repositories simultaneously:

1. **Initialize new repo**:

   ```bash
   curl -X POST http://localhost:12000/api/v1/config \
     -d '{"repo_root": "/path/to/new-repo"}'
   ```

2. **Run analysis on multiple repos**:

   ```bash
   # Repo A
   curl -X POST http://localhost:12000/api/v1/analyze \
     -d '{"repo_root": "/home/user/project-a", "entity": "Foo"}'

   # Repo B
   curl -X POST http://localhost:12000/api/v1/analyze \
     -d '{"repo_root": "/home/user/project-b", "entity": "Bar"}'
   ```

Each repo gets its own:

- `.compounding/` directory
- Isolated Qdrant collections (via project hash)
- Separate knowledge base entries

---

## Configuration

### Web UI

Visit `http://localhost:12000/api/v1/config` for a simple web UI to edit `.env` settings.

### Environment Variables

Edit `.env` file:

```env
# LLM Provider
DSPY_LM_PROVIDER=ollama
DSPY_LM_MODEL=qwen2.5vl:7b
OLLAMA_BASE_URL=http://localhost:11434/v1

# Infrastructure
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6350

# Server
HOST=127.0.0.1
PORT=12000
MCP_HOST=127.0.0.1
MCP_PORT=12001
```

---

## Troubleshooting

### No Celery Workers

**Symptom**: Tasks never complete, status stuck at "PENDING"

**Fix**:

```bash
# Check if workers are running
celery -A server.infrastructure.celery.app inspect active

# Start worker
celery -A server.infrastructure.celery.app worker --loglevel=info
```

### Redis Connection Refused

**Symptom**: "Connection refused to redis://localhost:6350"

**Fix**:

```bash
# Start Redis
docker compose up redis -d

# Check Redis is listening
docker compose ps redis
```

### Import Errors

**Symptom**: ModuleNotFoundError for server modules

**Fix**:

```bash
# Reinstall package
pip install -e .

# Or with uv
uv pip install -e .
```

---

## Architecture

```bash
┌─────────────────────────────────────────┐
│  MCP Client     HTTP Client   WebSocket │
│  (stdio)        (REST API)    (progress)│
└────────┬───────────┬─────────────┬──────┘
         │           │             │
         v           v             v
┌─────────────────────────────────────────┐
│         FastMCP      FastAPI            │
│         server.mcp   server.main        │
└────────┬───────────┬─────────────┬──────┘
         │           │             │
         └───────────┴─────────────┘
                     │
                     v
┌─────────────────────────────────────────┐
│      Application Services (DDD)         │
│      server.application.services.*      │
└────────┬────────────────────────────────┘
         │
         v
┌─────────────────────────────────────────┐
│           Celery Task Queue             │
│      server.infrastructure.celery.*     │
└────────┬────────────────────────────────┘
         │
         v
┌─────────────────────────────────────────┐
│      Workflow Orchestrators             │
│      workflows/*.py (existing)          │
└────────┬────────────────────────────────┘
         │
         v
┌─────────────────────────────────────────┐
│      DSPy Agents + Knowledge Base       │
│      agents/* + utils/knowledge/*       │
└─────────────────────────────────────────┘
```

---

## Development

### Running Tests

```bash
# TODO: Add tests
pytest tests/
```

### Code Quality

```bash
# Run linting and formatting
ruff check --fix server/
ruff format server/
```

### Adding New Commands

1. Create task in `server/infrastructure/celery/tasks/`
2. Create service in `server/application/services/`
3. Create API endpoint in `server/api/v1/`
4. Add MCP tool in `server/mcp/tools.py`
5. Update `server/api/api_router.py`

---

## Success Criteria (All Complete ✓)

- ✅ FastMCP server exposes all CLI commands as MCP tools
- ✅ FastAPI server accepts HTTP requests, returns task IDs
- ✅ Celery processes tasks asynchronously
- ✅ WebSocket streams real-time progress
- ✅ Multi-repo support with isolated `.compounding/` directories
- ✅ Simple web UI for .env configuration
- ✅ Docker Compose deployment with all services
- ✅ 100 lines/file limit enforced (DDD layers)
- ✅ No relative imports (absolute only)
- ✅ Ruff compliant code

---

## Next Steps

1. **Start Services**: `docker compose up server celery-worker -d`
2. **Test API**: `curl http://localhost:12000/health`
3. **Configure MCP**: Add to Claude Desktop config
4. **Test from Another Repo**: Call API with different `repo_root`
5. **Monitor Progress**: Use WebSocket connection for real-time updates
