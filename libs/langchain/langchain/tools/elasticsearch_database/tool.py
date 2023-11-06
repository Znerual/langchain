# flake8: noqa
"""Tools for interacting with an Elasticsearch database."""
from typing import Any, Dict, Optional, Type
import ast

from langchain.pydantic_v1 import BaseModel, Extra, Field, root_validator

from langchain.schema.language_model import BaseLanguageModel
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain.utilities.elasticsearch_database import ElasticsearchDatabase
from langchain.tools.base import BaseTool
from langchain.tools.elasticsearch_database.prompt import QUERY_CHECKER


class BaseElasticsearchDatabaseTool(BaseModel):
    """Base tool for interacting with an Elasticsearch database."""

    db: ElasticsearchDatabase = Field(exclude=True)

    class Config(BaseTool.Config):
        pass

class QueryElasticsearchDatabaseToolSchema(BaseModel):
    """Schema for QueryElasticsearchDatabaseTool."""

    query: str = Field(description="The search to run. Consisting of {index, query}.")

class QueryElasticsearchDatabaseTool(BaseElasticsearchDatabaseTool, BaseTool):
    """Tool for querying an Elasticsearch database."""

    name: str = "elasticsearch_db_query"
    description: str = """
    Input to this tool is the index of the Elasticsearch database index and a detailed and correct Elasticsearch search, "
    "output is a result from the database."
    The input has to be in the format of a dict, with the keys 'index' and 'query'.
    If the search is not correct, an error message will be returned.
    If an error is returned, rewrite the search, check the search, and try again.
    """
    args_schema: Type[QueryElasticsearchDatabaseToolSchema] = QueryElasticsearchDatabaseToolSchema
    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute the body on the given index, return the results or an error message."""
        string_valid  = False
        counter = 0
        while not string_valid:
            try:
                input_dict = ast.literal_eval(query)
                string_valid = True
            except ValueError as e:
                if counter > 0:
                    return f"ValueError {str(e)}: Input has to be in the format of a dict, with the keys 'index' and 'query'."
                sanitized_str = query.replace('index:', '"index":').replace('index :', '"index":').replace('query:', '"query":').replace('query :', '"query":')
                query = sanitized_str
                counter += 1
            except SyntaxError as e:
                print(f"SyntaxError: {e} for input {query}")
                return "SyntaxError: Input has to be in the format of a dict, with the keys index and query." 
        
        if not "index" in input_dict or not "query" in input_dict:
            return "Input has to be in the format of a dict, with the keys index and query." 
        
        return self.db.run_no_throw(input_dict["index"], {"query" : input_dict["query"]})


class InfoElasticsearchDatabaseTool(BaseElasticsearchDatabaseTool, BaseTool):
    """Tool for getting metadata about an Elasticsearch index."""

    name: str = "elasticsearch_index_schema"
    description: str = """
    Input to this tool is the name of an Elasticsearch index, and the output is the schema and sample documents from that index.
    """
   
    short_answer: bool = True
    def _run(
        self,
        index_name: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Get the schema and sample documents from an Elasticsearch index."""
        return self.db.get_table_info_no_throw(index_name, short_answer=self.short_answer)


class ListElasticsearchDatabaseTool(BaseElasticsearchDatabaseTool, BaseTool):
    """Tool for getting index names."""

    name: str = "elasticsearch_list_indices"
    description: str = "Input is an empty string, output is a comma separated list of indices in the database."

    def _run(
        self,
        tool_input: str = "",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Get the schema for a specific table."""
        return ", ".join(self.db.get_usable_table_names())


class QueryElasticsearchCheckerTool(BaseElasticsearchDatabaseTool, BaseTool):
    """Use an LLM to check if a query is correct.
    Adapted from https://www.patterns.app/blog/2023/01/18/crunchbot-sql-analyst-gpt/"""

    template: str = QUERY_CHECKER
    llm: BaseLanguageModel
    llm_chain: LLMChain = Field(init=False)
    name: str = "elasticsearch_db_query_checker"
    description: str = """
    Use this tool to double check if your query is correct before executing it.
    Always use this tool before executing a search with elasticsearch_db_query!
    """
    args_schema: Type[QueryElasticsearchDatabaseToolSchema] = QueryElasticsearchDatabaseToolSchema
    @root_validator(pre=True)
    def initialize_llm_chain(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if "llm_chain" not in values:
            values["llm_chain"] = LLMChain(
                llm=values.get("llm"),
                prompt=PromptTemplate(
                    template=QUERY_CHECKER, input_variables=["index", "query"]
                ),
            )

        if values["llm_chain"].prompt.input_variables != ["index", "query"]:
            raise ValueError(
                f"LLM chain for QueryCheckerTool must have input variables {'index', 'query'}, prompt was {values['llm_chain'].prompt}"
            )

        return values

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the LLM to check the query."""
        
        string_valid  = False
        counter = 0
        while not string_valid:
            try:
                input_dict = ast.literal_eval(query)
                string_valid = True
            except ValueError as e:
                if counter > 0:
                    return f"ValueError {str(e)}: Input has to be in the format of a dict, with the keys 'index' and 'query'."
                sanitized_str = query.replace('index:', '"index":').replace('index :', '"index":').replace('query:', '"query":').replace('query :', '"query":')
                query = sanitized_str
                counter += 1
            except SyntaxError as e:
                print(f"SyntaxError: {e} for input {query}")
                return "SyntaxError: Input has to be in the format of a dict, with the keys index and query." 
        
        if not "index" in input_dict or not "query" in input_dict:
            return "Input has to be in the format of a dict, with the keys index and query." 
        
        
        return self.llm_chain.predict(
            index=input_dict["index"],
            query=input_dict["query"],
            callbacks=run_manager.get_child() if run_manager else None,
        )

    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        
        string_valid  = False
        counter = 0
        while not string_valid:
            try:
                input_dict = ast.literal_eval(query)
                string_valid = True
            except ValueError as e:
                if counter > 0:
                    return f"ValueError {str(e)}: Input has to be in the format of a dict, with the keys 'index' and 'query'."
                sanitized_str = query.replace('index:', '"index":').replace('index :', '"index":').replace('query:', '"query":').replace('query :', '"query":')
                query = sanitized_str
                counter += 1
            except SyntaxError as e:
                print(f"SyntaxError: {e} for input {query}")
                return "SyntaxError: Input has to be in the format of a dict, with the keys index and query." 
        
        if not "index" in input_dict or not "query" in input_dict:
            return "Input has to be in the format of a dict, with the keys index and query." 
        
        return await self.llm_chain.apredict(
            index=input_dict["index"],
            query=input_dict["query"],
            callbacks=run_manager.get_child() if run_manager else None,
        )