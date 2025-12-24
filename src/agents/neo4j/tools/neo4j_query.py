"""Neo4j query tool."""

import os
from typing import Optional, Type

from langchain_core.tools import BaseTool
from neo4j import GraphDatabase
from pydantic import BaseModel, Field

from src.utils.logger import get_logger

logger = get_logger()


class Neo4jQueryInput(BaseModel):
    """Input for Neo4j query tool."""

    query: str = Field(..., description="Cypher query to execute")
    parameters: Optional[dict] = Field(
        default=None, description="Query parameters"
    )


class Neo4jQueryTool(BaseTool):
    """Tool for executing Cypher queries against Neo4j database."""

    name: str = "neo4j_query"
    description: str = (
        "Execute a Cypher query against Neo4j database. "
        "Use this to retrieve nodes, relationships, or perform graph analysis. "
        "Returns query results as a list of records."
    )
    args_schema: Type[BaseModel] = Neo4jQueryInput

    def _run(
        self, query: str, parameters: Optional[dict] = None
    ) -> list[dict]:
        """Execute the Cypher query."""
        try:
            uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            user = os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "")
            driver = GraphDatabase.driver(uri, auth=(user, password))
            with driver.session() as session:
                result = session.run(query, parameters or {})
                records = [dict(record) for record in result]
                logger.info(f"Neo4j query executed successfully. Returned {len(records)} records.")
                return records
        except Exception as e:
            logger.error(f"Neo4j query error: {e}")
            return [{"error": str(e)}]
        finally:
            if "driver" in locals():
                driver.close()


# Export tool instance
neo4j_query_tool = Neo4jQueryTool()

