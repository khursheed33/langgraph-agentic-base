# Fix: Supervisor Routing for Simple Queries and Exception Handling

## Changes Made

### 1. Fixed Greeting Routing (supervisor_agent.py)
- **Before:** Simple greetings like "hi" caused supervisor to end workflow and return generic greeting message
- **After:** Supervisor now routes simple greetings to `general_qa` agent, which generates appropriate responses
- **Line Changed:** 172-178

### 2. Fixed Classifier Fallback (supervisor_agent.py)
- **Before:** When classifier failed, always routed to planner (complex task planning)
- **After:** Classifier fallback now checks query complexity:
  - Simple queries (≤3 words or greetings) → routes to `general_qa`
  - Complex queries → routes to `planner`
- **Line Changed:** 181-191

### 3. Improved Exception Handling (supervisor_agent.py)
- **Before:** Any exception in supervisor immediately returned "technical difficulties"
- **After:** Exception handler now attempts fallback routing before giving up
  - Tries to intelligently route based on query complexity
  - Only returns error if fallback also fails
  - Logs full exception trace for debugging
- **Line Changed:** 216-235

### 4. Fixed General QA Import (general_qa_agent.py)
- **Added:** Missing `END_NODE` import (line 3)
- **Fixed:** NameError when general_qa tried to use END_NODE

## Flow Now

```
User Input: "hi"
    ↓
Supervisor: Classifies as "conversational" intent
    ↓
Router: Routes to general_qa (not ending workflow)
    ↓
General QA: Generates greeting response
    ↓
Workflow ends with general_qa's response
```

## Key Insight

The original design tried to have supervisor generate final responses for simple queries (ending workflow directly). This violates the separation of concerns:
- **Supervisor:** Routes to agents
- **Agents:** Generate responses
- **Supervisor should never generate final responses directly**

This fix ensures supervisor strictly routes queries to appropriate agents, which then generate the final responses.
