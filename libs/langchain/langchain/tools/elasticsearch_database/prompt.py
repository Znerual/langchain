# flake8: noqa
QUERY_CHECKER = """
{query}
Double check the search above for index {index} for common mistakes, including:
- Missing or mismatched curly braces.
- Typos or incorrect field names in the query DSL.
- The wildcard query is not supported in a "bool" query's filter context.
- Elasticsearch queries need to follow a specific structure, and incorrect nesting or order can lead to errors.
- Attempting to search for data with a query of a different data type.
- Using the correct number of arguments for functions.

If there are any of the above mistakes, rewrite the search. If there are no mistakes, just reproduce the original search.

Output the final Elasticsearch search only.

Elasticsearch search: """