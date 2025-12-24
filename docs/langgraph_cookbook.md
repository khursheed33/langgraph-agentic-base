# LangGraph Quickstart — README

This example shows how to build a **calculator agent** with LangGraph using both:

✅ Graph API (node/edge based workflow)
✅ Functional API (single function loop)

Requires:

* A Claude (Anthropic) API key in your environment:

  ```
  export ANTHROPIC_API_KEY="your_api_key_here"
  ```

  ([LangChain Docs][1])

---

## 🛠️ Dependencies

```bash
pip install langgraph langchain
```

---

## 📌 Graph API — Full Example

### 1️⃣ Define model and tools

```python
from langchain.tools import tool
from langchain.chat_models import init_chat_model

model = init_chat_model(
    "claude-sonnet-4-5-20250929",
    temperature=0
)

# Define simple arithmetic tools
@tool
def add(a: int, b: int) -> int:
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    return a * b

@tool
def divide(a: int, b: int) -> float:
    return a / b

tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}

# Bind tools to the model
model_with_tools = model.bind_tools(tools)
```

---

### 2️⃣ Define shared state

```python
from langchain.messages import AnyMessage
from typing_extensions import TypedDict, Annotated
import operator

class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int
```

---

### 3️⃣ Model node (call the LLM)

```python
from langchain.messages import SystemMessage

def llm_call(state: dict):
    return {
        "messages": [
            model_with_tools.invoke(
                [SystemMessage(content="You are a helpful assistant tasked with performing arithmetic.")]
                + state["messages"]
            )
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }
```

---

### 4️⃣ Tool node (execute tools)

```python
from langchain.messages import ToolMessage

def tool_node(state: dict):
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}
```

---

### 5️⃣ Logic to continue or end

```python
from typing import Literal
from langgraph.graph import StateGraph, START, END

def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tool_node"
    return END
```

---

### 6️⃣ Build and run the graph

```python
agent_builder = StateGraph(MessagesState)

# Add nodes
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

# Connect nodes
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
agent_builder.add_edge("tool_node", "llm_call")

# Compile
agent = agent_builder.compile()

# Invoke
from langchain.messages import HumanMessage

messages = [HumanMessage(content="Add 3 and 4.")]
result_state = agent.invoke({"messages": messages})

for message in result_state["messages"]:
    message.pretty_print()
```

---

## 🌀 Functional API Version

This variant defines the same logic inside a function using LangGraph decorators:

```python
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage
from langchain.messages import SystemMessage, HumanMessage, ToolCall
from langgraph.func import entrypoint, task
from langgraph.graph import add_messages

# same model & tools setup
model = init_chat_model(...)
# define add/multiply/divide as above
model_with_tools = model.bind_tools([add, multiply, divide])

@task
def call_llm(messages: list[BaseMessage]):
    return model_with_tools.invoke(
        [SystemMessage(content="You are a helpful AI agent.")]
        + messages
    )

@task
def call_tool(tool_call: ToolCall):
    tool = tools_by_name[tool_call["name"]]
    return tool.invoke(tool_call)

@entrypoint()
def agent(messages: list[BaseMessage]):
    response = call_llm(messages).result()

    while response.tool_calls:
        # execute each tool call
        tool_results = [call_tool(tc).result() for tc in response.tool_calls]
        messages = add_messages(messages, [response, *tool_results])
        response = call_llm(messages).result()

    return add_messages(messages, response)

# run agent
messages = [HumanMessage(content="Add 3 and 4.")]
for output in agent.stream(messages, stream_mode="updates"):
    print(output)
```
