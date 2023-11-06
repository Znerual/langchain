from elasticsearch import Elasticsearch
from typing import Union, Literal, Dict, Any, Sequence, Optional, List
import warnings

class ElasticsearchDatabase:
    def __init__(self, host, **kwargs):
        self.client = Elasticsearch(host, **kwargs)

    
        
    def get_usable_table_names(self):
        import warnings
        try:
            
            # ignore the warning that says that we access the system index
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                indices = self.client.indices.get_alias().keys()
            indices = [ind for ind in indices if not ind.startswith(".security")] # remove the system index
            return sorted(indices)
        except Exception as e:
            return f"Error: {e}"

    def get_table_names(self):
        warnings.warn("This method is deprecated - please use `get_usable_table_names`.")
        return self.get_usable_table_names()
    
    def _get_sample_documents(self, index_name, size=3):
        try:
            # Search for sample documents in the specified index
            query = {
                "size": size,
                "query": {
                    "match_all": {}  # You can adjust the query as needed
                }
            }
            response = self.client.search(index=index_name, body=query)
            sample_docs = response['hits']['hits']

            # Extract and format the sample document fields
            MAX_LENGTH = 512
            max_field_length = MAX_LENGTH // len(sample_docs)
            sample_rows = []
            for doc in sample_docs:
                doc_source = doc['_source']
                sample_row = ", ".join([str(doc_source.get(field, ''))[:max_field_length] for field in doc_source])
                sample_rows.append(sample_row)

            return ', '.join(sample_rows)
        except Exception as e:
            return f"Error: {e}"

    def _simplify_mapping(self, mapping):
        if 'properties' in mapping:
            return self._simplify_mapping(mapping['properties'])

        if 'type' in mapping:
            return mapping['type']

        # Handle cases where 'properties' or 'type' is missing
        if isinstance(mapping, dict):
            return {key: self._simplify_mapping(value) for key, value in mapping.items()}

        return mapping

    def get_table_info(self, index_name,  short_answer:bool=False):
        try:
            mapping = self.client.indices.get_mapping(index=index_name)[index_name]['mappings']
            
            # Simplify the mapping information
            mapping = self._simplify_mapping(mapping)
            
            if short_answer:
                return str(mapping)
            
            # Get sample documents from the index
            sample_rows = self._get_sample_documents(index_name, size=1)
            # Process and format the mapping information as needed
            return str(mapping) + "\n" + str(sample_rows)
        except Exception as e:
            return f"Error: {e}"
        
    def _execute(self, index:str, query: dict, fetch: Union[Literal["all"], Literal["one"]] = "all") -> Sequence[Dict[str, Any]]:
        try:
            # Execute the Elasticsearch query
            response = self.client.search(index=index, body=query)

            if fetch == "all":
                result = [hit["_source"] for hit in response["hits"]["hits"]]
            elif fetch == "one":
                result = [response["hits"]["hits"][0]["_source"]] if response["hits"]["total"]["value"] > 0 else []
            else:
                raise ValueError("Fetch parameter must be either 'one' or 'all")

            return result
        except Exception as e:
            return f"Error: {str(e)}"

    def run(self, index:str, query: dict, fetch: Union[Literal["all"], Literal["one"]] = "all") -> str:
        result = self._execute(index, query, fetch)
        if not result:
            return ""
        elif result.startswith("Error:"):
            return result
        
        else:
            # Format the results as a string
            formatted_result = "\n".join([str(row) for row in result])
            return formatted_result
        
    def get_table_info_no_throw(self, table_names: Optional[List[str]] = None, short_answer:bool = False) -> str:
        """Get information about specified tables.

        Follows best practices as specified in: Rajkumar et al, 2022
        (https://arxiv.org/abs/2204.00498)

        If `sample_rows_in_table_info`, the specified number of sample rows will be
        appended to each table description. This can increase performance as
        demonstrated in the paper.
        """
        try:
            return self.get_table_info(table_names, short_answer=short_answer)
        except ValueError as e:
            """Format the error message"""
            return f"Error: {str(e)}"

    def run_no_throw(
        self,
        index: str,
        command: str,
        fetch: Union[Literal["all"], Literal["one"]] = "all",
    ) -> str:
        """Execute an Elasticsearch command on a given index and return a string representing the results.

        If the statement returns rows, a string of the results is returned.
        If the statement returns no rows, an empty string is returned.

        If the statement throws an error, the error message is returned.
        """
        try:
            return self.run(index, command, fetch)
        except Exception as e:
            """Format the error message"""
            return f"Error: {str(e)}"
