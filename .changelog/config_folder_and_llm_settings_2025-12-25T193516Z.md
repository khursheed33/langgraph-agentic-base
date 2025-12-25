# Config Folder and LLM Settings

- Created src/config/ folder for centralized configuration
- Moved agents.yaml to src/config/agents.yaml
- Created comprehensive src/config/config.yaml with LLM, workflow, Neo4j, logging, agent, and task persistence settings
- Updated AgentMetadataLoader to load from src/config/agents.yaml
- Updated SettingsManager to load defaults from config.yaml (env vars still take precedence)
- Added LLM configuration properties: provider, model, temperature, max_tokens, max_input_tokens, top_p, timeout
- Updated LLMInstance to use config.yaml settings for temperature, max_tokens, and timeout
- Config.yaml includes settings for: LLM (provider, model, tokens, temperature), workflow (max_iterations, retries), Neo4j, logging, agents, and task persistence

