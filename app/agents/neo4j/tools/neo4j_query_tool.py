"""Neo4j query tool."""

from typing import Optional, Type

from langchain_core.tools import BaseTool
from neo4j import GraphDatabase
from pydantic import BaseModel, Field

from app.utils.logger import logger
from app.utils.settings import settings


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
            uri = settings.NEO4J_URI
            user = settings.NEO4J_USER
            password = settings.NEO4J_PASSWORD
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

