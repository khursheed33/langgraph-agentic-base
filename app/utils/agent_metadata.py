"""Agent metadata loader for dynamic agent discovery.

This module loads agent metadata from agents.yaml config file and provides
utilities to format agent information for prompts.
"""

from pathlib import Path

import yaml

from app.utils.logger import logger


class AgentMetadata:
    """Agent metadata container."""

    def __init__(
        self,
        name: str,
        description: str,
        capabilities: list[str] | None = None,
        use_cases: list[str] | None = None,
    ) -> None:
        """Initialize agent metadata."""
        self.name = name
        self.description = description
        self.capabilities = capabilities or []
        self.use_cases = use_cases or []

    def to_supervisor_format(self) -> str:
        """Format agent info for supervisor prompt."""
        return f"- **{self.name}**: {self.description}"

    def to_planner_format(self) -> str:
        """Format agent info for planner prompt."""
        lines = [f"### {self.name}"]
        lines.append(f"- {self.description}")
        
        if self.capabilities:
            for cap in self.capabilities:
                lines.append(f"- {cap}")
        
        if self.use_cases:
            use_cases_str = ", ".join(self.use_cases)
            lines.append(f"- Use for: {use_cases_str}")
        
        return "\n".join(lines)


class AgentMetadataLoader:
    """Loader for agent metadata from config file."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        """Initialize loader with config file path."""
        if config_path is None:
            # Try to find agents.yaml in src/config folder
            src_dir = Path(__file__).parent.parent
            config_path = src_dir / "config" / "agents.yaml"
        
        self.config_path = Path(config_path)
        self._metadata_cache: dict[str, AgentMetadata] | None = None

    def load_metadata(self) -> dict[str, AgentMetadata]:
        """Load agent metadata from config file."""
        if self._metadata_cache is not None:
            return self._metadata_cache

        if not self.config_path.exists():
            logger.warning(
                f"Agent config file not found: {self.config_path}. "
                "Using fallback metadata."
            )
            return self._get_fallback_metadata()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            agents_config = config.get("agents", {})
            metadata: dict[str, AgentMetadata] = {}

            for agent_name, agent_config in agents_config.items():
                metadata[agent_name] = AgentMetadata(
                    name=agent_config.get("name", agent_name),
                    description=agent_config.get("description", ""),
                    capabilities=agent_config.get("capabilities", []),
                    use_cases=agent_config.get("use_cases", []),
                )

            logger.info(f"Loaded metadata for {len(metadata)} agents from {self.config_path}")
            self._metadata_cache = metadata
            return metadata

        except Exception as e:
            logger.error(f"Failed to load agent metadata: {e}")
            return self._get_fallback_metadata()

    def _get_fallback_metadata(self) -> dict[str, AgentMetadata]:
        """Get fallback metadata when config file is not available."""
        return {
            "planner": AgentMetadata(
                name="planner",
                description="Creates a task plan based on user intent and available agent capabilities",
            ),
            "neo4j": AgentMetadata(
                name="neo4j",
                description="Query and analyze Neo4j graph database. Can build Cypher queries from user input, execute them, and format results. Can retrieve nodes, relationships, and perform graph analysis.",
            ),
            "filesystem": AgentMetadata(
                name="filesystem",
                description="Read and write files, create directories, and manage file system operations.",
            ),
            "general_qa": AgentMetadata(
                name="general_qa",
                description="Handle general conversational queries, greetings, questions, and provide friendly responses to user inputs.",
            ),
        }

    def get_available_agents(self, exclude: list[str] | None = None) -> dict[str, AgentMetadata]:
        """Get available agents excluding specified ones."""
        exclude = exclude or []
        metadata = self.load_metadata()
        return {
            name: meta for name, meta in metadata.items()
            if name not in exclude
        }

    def format_for_supervisor(self, exclude: list[str] | None = None) -> str:
        """Format agent metadata for supervisor prompt."""
        exclude = exclude or ["supervisor"]
        agents = self.get_available_agents(exclude=exclude)
        
        # Sort agents: planner first, then others alphabetically
        sorted_agents = sorted(
            agents.items(),
            key=lambda x: (x[0] != "planner", x[0])
        )
        
        lines = []
        for _, metadata in sorted_agents:
            lines.append(metadata.to_supervisor_format())
        
        return "\n".join(lines)

    def format_for_planner(self, exclude: list[str] | None = None) -> str:
        """Format agent metadata for planner prompt."""
        exclude = exclude or ["supervisor", "planner"]
        agents = self.get_available_agents(exclude=exclude)
        
        # Sort agents alphabetically
        sorted_agents = sorted(agents.items(), key=lambda x: x[0])
        
        lines = []
        for _, metadata in sorted_agents:
            lines.append(metadata.to_planner_format())
        
        return "\n\n".join(lines)

    def get_agent_names_list(self, exclude: list[str] | None = None) -> list[str]:
        """Get list of agent names for JSON schema validation."""
        exclude = exclude or []
        agents = self.get_available_agents(exclude=exclude)
        return sorted(agents.keys())


# Global loader instance
_loader: AgentMetadataLoader | None = None


def get_agent_metadata_loader() -> AgentMetadataLoader:
    """Get or create global agent metadata loader."""
    global _loader
    if _loader is None:
        _loader = AgentMetadataLoader()
    return _loader

