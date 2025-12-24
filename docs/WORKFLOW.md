# Workflow Management and Compilation

## Where LangGraph Workflow is Managed

The LangGraph workflow is managed and compiled in **`src/workflow/graph.py`** in the `create_workflow()` function.

### Workflow Compilation Location

```python
# src/workflow/graph.py

def create_workflow() -> Any:
    """Create and configure the LangGraph workflow with dynamic routing."""
    # ... workflow setup ...
    
    # Compile workflow - THIS IS WHERE THE GRAPH IS COMPILED
    app = workflow.compile()
    return app
```

The workflow compilation happens at **line 90** in `src/workflow/graph.py` when `workflow.compile()` is called.

## Dynamic Routing Implementation

The routing system is **completely dynamic** - no hardcoded agent names are used. Here's how it works:

### 1. Agent Registry (`src/agents/registry.py`)

All agents are registered in a central registry:

```python
AGENT_REGISTRY: dict[str, Type[BaseAgent]] = {
    AgentType.SUPERVISOR: SupervisorAgent,
    AgentType.PLANNER: PlannerAgent,
    AgentType.NEO4J: Neo4jAgent,
    AgentType.FILESYSTEM: FileSystemAgent,
}
```

### 2. Dynamic Node Addition

Nodes are added dynamically based on the registry:

```python
# Get all available agents from registry
available_agents = get_available_agent_types()

# Dynamically add each agent as a node
for agent_type in available_agents:
    agent_executor = get_agent_executor(agent_type)
    workflow.add_node(agent_type, agent_executor)
```

### 3. Dynamic Routing Map

The routing map is built dynamically:

```python
def get_routing_map() -> dict[str, str]:
    """Get dynamic routing map for all registered agents."""
    routing_map: dict[str, str] = {}
    
    # Add all available agents dynamically
    for agent_type in get_available_agent_types():
        routing_map[agent_type] = agent_type
    
    return routing_map
```

### 4. Dynamic Conditional Edges

Routing decisions are made dynamically based on state:

```python
def route_after_supervisor(state: AgentState) -> str:
    """Dynamic routing function - no hardcoded agent names."""
    if state.current_agent is None or state.current_agent == END_NODE:
        return END_NODE
    
    agent_name = state.current_agent
    
    # Validate dynamically
    if agent_name not in available_agents and agent_name != END_NODE:
        logger.error(f"Unknown agent in routing: {agent_name}")
        return END_NODE
    
    return agent_name  # Dynamic routing
```

### 5. Dynamic Edge Creation

All edges are created dynamically:

```python
# All agents (except supervisor) return to supervisor
# This is dynamic - any agent in the registry will automatically route back
for agent_type in available_agents:
    if agent_type != AgentType.SUPERVISOR.value:
        workflow.add_edge(agent_type, AgentType.SUPERVISOR.value)
```

## Adding New Agents

To add a new agent without modifying routing code:

1. **Create the agent** in `src/agents/your_agent/`
2. **Register it** in `src/agents/registry.py`:
   ```python
   AGENT_REGISTRY[AgentType.YOUR_AGENT] = YourAgentClass
   ```
3. **Add to constants** in `src/constants.py`:
   ```python
   class AgentType(str, Enum):
       YOUR_AGENT = "your_agent"
   ```
4. **That's it!** The workflow will automatically:
   - Discover the new agent
   - Add it as a node
   - Include it in routing
   - Route back to supervisor

## Workflow Execution Flow

1. **Entry Point**: Supervisor (set dynamically)
2. **Supervisor** → Routes based on `state.current_agent` (dynamic)
3. **Planner/Task Agents** → Execute and return to Supervisor
4. **Supervisor** → Checks completion and routes accordingly
5. **End** → When `current_agent == "__end__"`

## References

- [LangGraph Quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart)
- [LangGraph Graph API Overview](https://docs.langchain.com/oss/python/langgraph/overview)

