# Rename Query Agent to General QA Agent

- Renamed agent folder from query to general_qa
- Renamed QueryAgent class to GeneralQAAgent
- Renamed query.py file to general_qa.py
- Updated AgentType enum: QUERY -> GENERAL_QA
- Updated all imports and references in registry.py
- Updated agents.yaml config: query -> general_qa
- Updated agent_metadata.py fallback metadata
- Updated planner prompt.md references to use general_qa agent name
- Updated general_qa agent prompt.md title and description
- Updated all role names from "query" to "general_qa" in agent execution

