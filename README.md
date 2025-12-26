# LangGraph Agentic Base

A LangGraph-based multi-agent system with supervisor and task planner capabilities. This project demonstrates a sophisticated agentic workflow where agents collaborate to complete complex tasks.

**Author:** Khursheed Gaddi (gaddi33khursheed@gmail.com)

## Features

- **LangGraph Integration**: Uses LangGraph StateGraph for workflow management
- **Multi-Agent System**: Supervisor, Planner, Neo4j, and FileSystem agents
- **Type Safety**: Full type annotations throughout the codebase
- **Singleton Patterns**: Logger and LLM instances use singleton pattern
- **Status Tracking**: Comprehensive tracking of agent and tool usage
- **Rich CLI**: Interactive console interface using Rich library
- **Structured Output**: Pydantic models for all agent outputs

## Project Structure

```
langgraph-agentic-base/
├── src/
│   ├── agents/
│   │   ├── supervisor/
│   │   │   ├── tools/
│   │   │   ├── prompt.md
│   │   │   └── supervisor.py
│   │   ├── planner/
│   │   │   ├── tools/
│   │   │   ├── prompt.md
│   │   │   └── planner.py
│   │   ├── neo4j/
│   │   │   ├── tools/
│   │   │   │   └── neo4j_query.py
│   │   │   ├── prompt.md
│   │   │   └── neo4j.py
│   │   ├── filesystem/
│   │   │   ├── tools/
│   │   │   │   └── file_operations.py
│   │   │   ├── prompt.md
│   │   │   └── filesystem.py
│   │   └── base_agent.py
│   ├── models/
│   │   ├── state.py
│   │   ├── supervisor.py
│   │   └── planner.py
│   ├── llm/
│   │   └── llm_instance.py
│   ├── workflow/
│   │   └── graph.py
│   ├── utils/
│   │   └── logger.py
│   └── constants.py
├── docs/
├── logs/
├── tasks/
├── main.py
├── cli.py
├── pyproject.toml
└── README.md
```

## Installation

### Prerequisites

- Python 3.12 or higher
- Groq API key (or OpenAI/Anthropic API key)
- (Optional) Neo4j database for Neo4j agent

### Docker Installation (Recommended)

For the easiest setup using Docker, see **[startup.md](startup.md)** and **[deployment/README.md](deployment/README.md)** for complete instructions.

Quick start:
```bash
# 1. Copy environment file
cp .env.example .env

# 2. Edit .env and add your API keys
# At minimum, set: GROQ_API_KEY=your_key_here

# 3. Start dependencies first
cd deployment
docker-compose -f docker-compose.dependencies.yml up -d

# 4. Start the application
docker-compose -f docker-compose.yml up -d

# 5. Access API at http://localhost:3301
```

**Note:** All Docker-related files are in the `deployment/` folder:
- `deployment/Dockerfile` - Application Docker image
- `deployment/docker-compose.yml` - Main application service
- `deployment/docker-compose.dependencies.yml` - Dependencies (Neo4j, etc.)

Docker Compose automatically reads the `.env` file from the project root. See [startup.md](startup.md) and [deployment/README.md](deployment/README.md) for detailed Docker setup instructions.

### Local Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd langgraph-agentic-base
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Create a `.env` file:
```bash
cp .env.example .env
```

5. Configure your `.env` file:
```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-70b-versatile

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password_here

LOG_LEVEL=INFO
MAX_ITERATIONS=50
```

## Usage

### CLI Mode (Interactive)

Run the interactive CLI:
```bash
python cli.py
```

This will start an interactive session where you can enter requests.

### Command Line Mode

Run with a single command:
```bash
python cli.py "analyze the graph and save the result in analysis.md"
```

### Programmatic Usage

```python
from main import run_workflow

result = run_workflow("your user input here")
print(result)
```

## Workflow Example

Example flow for: "analyze the graph and save the result in analysis.md"

1. **Supervisor** → Analyzes user intent, routes to Planner (no task list exists)
2. **Planner** → Creates task list:
   - Task 1: Neo4j agent - "Get few nodes from each label and analyze it"
   - Task 2: FileSystem agent - "Write analysis results to analysis.md"
3. **Supervisor** → Routes to Neo4j agent (first pending task)
4. **Neo4j Agent** → Executes Cypher queries, analyzes graph
5. **Supervisor** → Routes to FileSystem agent (next pending task)
6. **FileSystem Agent** → Writes results to analysis.md
7. **Supervisor** → All tasks completed, ends workflow
8. **Result** → Returns structured result with usage statistics

## Agents

### Supervisor Agent
- Analyzes user intent
- Routes tasks to appropriate agents
- Manages workflow execution
- Ends workflow when all tasks are completed

### Planner Agent
- Creates task plans based on user intent
- Knows all available agents and their capabilities
- Breaks down complex requests into manageable tasks

### Neo4j Agent
- Queries Neo4j graph database
- Builds Cypher queries from user input
- Performs graph analysis
- Formats and structures query results
- Uses Cypher query tool

### FileSystem Agent
- Reads and writes files
- Creates directories
- Manages file operations

## Status Tracking

The system tracks:
- **Agent Usage**: How many times each agent was used
- **Tool Usage**: How many times each tool was used
- **Task Status**: Status of each task (pending, in_progress, completed, failed)

All statistics are included in the final result for traceability.

## Logging

All operations are logged to `logs/timestamp_log.log` with timestamps. Log level can be configured via `LOG_LEVEL` environment variable.

## Development

### Code Style

The project follows Python best practices:
- Type hints throughout
- Singleton patterns for shared resources
- Enum constants for fixed values
- Pydantic models for data validation
- Proper error handling

### Adding New Agents

1. Create agent directory: `src/agents/your_agent/`
2. Create `prompt.md` with agent instructions
3. Create `tools/` directory with tool implementations
4. Create `your_agent.py` inheriting from `BaseAgent`
5. Add agent to workflow in `src/workflow/graph.py`
6. Update `src/constants.py` with agent type and capabilities

### Adding New Tools

1. Create tool file in agent's `tools/` directory
2. Inherit from `langchain_core.tools.BaseTool`
3. Export tool instance in `tools/__init__.py`
4. Tool will be automatically loaded by the agent

## Configuration

### Environment Variables

Docker Compose automatically reads environment variables from the `.env` file in the project root. You can also set them as shell environment variables (which take precedence).

**LLM Configuration** (at least one required):
- `GROQ_API_KEY`: Your Groq API key
- `OPENAI_API_KEY`: Your OpenAI API key
- `ANTHROPIC_API_KEY`: Your Anthropic API key

**Neo4j Configuration**:
- `NEO4J_URI`: Default: `bolt://neo4j:7687` (use `bolt://neo4j:7687` for Docker)
- `NEO4J_USER`: Default: `neo4j`
- `NEO4J_PASSWORD`: Default: `password` (change in production!)
- `NEO4J_AUTH`: Format: `username/password`, Default: `neo4j/password`

**API Configuration**:
- `API_HOST`: Default: `0.0.0.0`
- `API_PORT`: Default: `3301`

**Other**:
- `LOG_LEVEL`: Default: `INFO`
- `MAX_ITERATIONS`: Default: `50`

See [startup.md](startup.md) for detailed Docker setup instructions.

## Troubleshooting

### Common Issues

1. **GROQ_API_KEY not found**: Make sure `.env` file exists and contains your API key
2. **Neo4j connection errors**: Verify Neo4j is running and credentials are correct
3. **Import errors**: Ensure all dependencies are installed: `pip install -e .`

## License

This project is licensed under the Apache License 2.0. See [LICENSE.md](LICENSE.md) for details.

## Author

**Khursheed Gaddi**  
Email: gaddi33khursheed@gmail.com

## Workflow Management

The LangGraph workflow is compiled in **`src/workflow/graph.py`** in the `create_workflow()` function. The routing is completely dynamic - no hardcoded agent names are used. See [WORKFLOW.md](docs/WORKFLOW.md) for detailed information.

### Key Points:
- **Workflow Compilation**: `src/workflow/graph.py` line 90 (`workflow.compile()`)
- **Dynamic Routing**: All routing is based on the agent registry (`src/agents/registry.py`)
- **No Hardcoding**: Agents are discovered dynamically from the registry

## References

- [LangGraph Quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart)
- [LangGraph Documentation](https://docs.langchain.com/oss/python/langgraph/overview)
- [LangChain Documentation](https://python.langchain.com/)
- [Groq API](https://groq.com/)
- [Workflow Documentation](docs/WORKFLOW.md)

