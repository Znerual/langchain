"""Toolkit for interacting with an Elasticsearch database."""
from typing import List

from langchain.agents.agent_toolkits.base import BaseToolkit
from langchain.pydantic_v1 import Field
from langchain.schema.language_model import BaseLanguageModel
from langchain.tools import BaseTool
from langchain.tools.elasticsearch_database.tool import (
    InfoElasticsearchDatabaseTool,
    ListElasticsearchDatabaseTool,
    QueryElasticsearchCheckerTool,
    QueryElasticsearchDatabaseTool,
)
from langchain.utilities.elasticsearch_database import ElasticsearchDatabase


class ElasticsearchDatabaseToolkit(BaseToolkit):
    """Toolkit for interacting with Elasticsearch databases."""

    db: ElasticsearchDatabase = Field(exclude=True)
    llm: BaseLanguageModel = Field(exclude=True)

    class Config:
        """Configuration for this pydantic object."""

        arbitrary_types_allowed = True

    def get_tools(self) -> List[BaseTool]:
        """Get the tools in the toolkit."""
        list_elasticsearch_database_tool_description = (
            "Input is an empty string, output is a comma separated list of indices in the database."
        )
        list_elasticsearch_database_tool = ListElasticsearchDatabaseTool(db=self.db, description=list_elasticsearch_database_tool_description)
        
        info_elasticsearch_database_tool_description = (
            "Input to this tool is the name of an Elasticsearch index, and the output is the schema and sample documents from that index."
        )
        info_elasticsearch_database_tool = InfoElasticsearchDatabaseTool(
            db=self.db, description=info_elasticsearch_database_tool_description
        )
        query_elasticsearch_database_tool_description = (
            "Input to this tool is the Elasticsearch index and a detailed and correct Elasticsearch query, output is a "
            "result from the database. If the query is not correct, an error message "
            "will be returned. If an error is returned, rewrite the query, check the "
            "query, and try again. If you encounter an issue with 'index_not_found_exception' "
            f", use {list_elasticsearch_database_tool.name} to query the correct index."
            f" If the output is empty, use {info_elasticsearch_database_tool_description} "
            " to check if the field names are correct. If the output is still empty, use fuzzy "
            " to match the query. If the output is still empty, return 'I don't know'."
        )
        query_elasticsearch_database_tool = QueryElasticsearchDatabaseTool(
            db=self.db, description=query_elasticsearch_database_tool_description
        )
        query_elasticsearch_checker_tool_description = (
            "Use this tool to double check if your query is correct before executing "
            "it. Always use this tool before executing a query with "
            f"{query_elasticsearch_database_tool.name}!"
        )
        query_elasticsearch_checker_tool = QueryElasticsearchCheckerTool(
            db=self.db, llm=self.llm, description=query_elasticsearch_checker_tool_description
        )
        return [
            query_elasticsearch_database_tool,
            info_elasticsearch_database_tool,
            list_elasticsearch_database_tool,
            query_elasticsearch_checker_tool,
        ]