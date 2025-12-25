# Dynamic Agent Discovery

- Created agents.yaml config file for agent metadata (name, description, capabilities, use_cases)
- Implemented AgentMetadataLoader utility to load and parse agent configs dynamically
- Updated SupervisorAgent to inject agent info into prompt template dynamically
- Updated PlannerAgent to inject agent info into prompt template dynamically
- Modified supervisor and planner prompt.md templates to use placeholders for agent information
- Added pyyaml dependency to pyproject.toml
- Supervisor and planner now automatically discover agents from agents.yaml without code changes

