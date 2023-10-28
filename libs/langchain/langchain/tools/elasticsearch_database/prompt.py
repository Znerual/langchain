# flake8: noqa
QUERY_CHECKER = """
{query}
Double check the query for index {index} above for common mistakes, including:
- Missing or mismatched curly braces.
- Typos or incorrect field names in the query DSL.
- The wildcard query is not supported in a "bool" query's filter context.
- Elasticsearch queries need to follow a specific structure, and incorrect nesting or order can lead to errors.
- Attempting to search for data with a query of a different data type.
- Using the correct number of arguments for functions.
- Casting to the correct data type.
- When field names in the query are ambiguous and could refer to multiple fields.

If there are any of the above mistakes, rewrite the query. If there are no mistakes, just reproduce the original query.

Output the final Elasticsearch query only.

Elasticsearch Query: """