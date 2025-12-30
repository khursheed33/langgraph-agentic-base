# LangGraph Cookbook Compatibility

This document explains how our implementation aligns with the LangGraph cookbook patterns and the changes made to ensure compatibility.

## Key Changes Made

### 1. State Definition (Following Cookbook Pattern)

**Cookbook Pattern:**
```python
from typing_extensions import TypedDict, Annotated
import operator

class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int
```

**Our Implementation:**
- Created `AgentStateTyped` in `src/models/state_typed.py` using TypedDict
- Uses `Annotated[list[dict[str, Any]], operator.add]` for messages (automatic merging)
- Maintains Pydantic models (`AgentState`) for validation and type safety
- Converts between formats using wrapper functions

### 2. Node Return Format (Following Cookbook Pattern)

**Cookbook Pattern:**
```python
def llm_call(state: dict):
    return {
        "messages": [...],
        "llm_calls": state.get("llm_calls", 0) + 1
    }
```

**Our Implementation:**
- Nodes return `dict` with partial state updates (not full state objects)
- Created wrapper functions in `src/workflow/graph.py` to convert:
  - Input: `dict` state → Pydantic `AgentState`
  - Execute: Agent returns `tuple[AgentState, UsageStats]`
  - Output: Convert back to `dict` with only changed fields
- LangGraph automatically merges partial updates

### 3. StateGraph Usage (Following Cookbook Pattern)

**Cookbook Pattern:**
```python
agent_builder = StateGraph(MessagesState)
agent_builder.add_node("llm_call", llm_call)
agent = agent_builder.compile()
```

**Our Implementation:**
- Uses `StateGraph(AgentStateTyped)` with TypedDict state
- Dynamically adds nodes from agent registry
- Compiles graph: `workflow.compile()` (line 90 in `src/workflow/graph.py`)
- Follows exact cookbook pattern for graph construction

### 4. Conditional Edges (Following Cookbook Pattern)

**Cookbook Pattern:**
```python
def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tool_node"
    return END

agent_builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
```

**Our Implementation:**
- Routing function accepts `dict` state (not Pydantic)
- Returns string node names dynamically from registry
- Uses dynamic routing map built from agent registry
- No hardcoded agent names

## Architecture Decisions

### Why Keep Pydantic Models?

1. **Type Safety**: Pydantic provides runtime validation
2. **Developer Experience**: Easier to work with in agent code
3. **Documentation**: Self-documenting with Field descriptions
4. **Compatibility**: Convert to/from TypedDict as needed

### Conversion Strategy

```
LangGraph StateGraph (TypedDict)
    ↓ (wrapper converts dict → Pydantic)
Agent Execute Methods (Pydantic)
    ↓ (returns tuple)
Wrapper (converts tuple → dict)
    ↓ (returns partial updates)
LangGraph merges updates
```

## Files Modified

1. **`src/models/state_typed.py`** (NEW)
   - TypedDict state definition for LangGraph compatibility
   - Uses `Annotated` with `operator.add` for message merging

2. **`src/workflow/graph.py`**
   - Updated to use `AgentStateTyped` instead of `AgentState`
   - Added node wrapper functions for format conversion
   - Routing function now accepts `dict` instead of Pydantic

3. **`main.py`**
   - Converts Pydantic to dict for workflow invocation
   - Converts dict back to Pydantic for result processing

4. **`cli.py`**
   - Same conversion pattern as `main.py`

## Benefits

1. ✅ **LangGraph Compatibility**: Follows official cookbook patterns
2. ✅ **Type Safety**: Maintains Pydantic validation
3. ✅ **Dynamic Routing**: No hardcoded agent names
4. ✅ **Automatic Merging**: Messages merge via `operator.add`
5. ✅ **Partial Updates**: Only changed fields returned (efficient)

## Testing Compatibility

To verify compatibility:

```python
from app.workflow import create_workflow
from app.models.state_typed import AgentStateTyped

app = create_workflow()

# Initialize state as dict (cookbook pattern)
state: AgentStateTyped = {
    "user_input": "test",
    "messages": [],
    # ... other fields
}

# Invoke (cookbook pattern)
result = app.invoke(state)
```

## References

- [LangGraph Quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart)
- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/overview)

