TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_arxiv",
            "description": "Search ArXiv papers using semantic and sparse vector search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query text",
                    },
                    "arxiv_id": {
                        "type": "string",
                        "description": "The arxiv paper id",
                    },
                },
                "required": ["query", "arxiv_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_by_arxiv_id",
            "description": "Retrieve a single ArXiv paper by its exact arXiv ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "arxiv_id": {
                        "type": "string",
                        "description": "The exact arXiv identifier of the paper (e.g., '2301.12345')",
                    },
                },
                "required": ["arxiv_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_papers_by_name",
            "description": (
                "Search the SQL database for papers whose title contains the given text "
                "(case-insensitive). Use when the user describes a paper by name or partial title "
                "and does not give an exact arXiv ID. Returns metadata so the user can confirm "
                "which paper they meant."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title_query": {
                        "type": "string",
                        "description": (
                            "Words or phrase from the paper title to match (substring search)"
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of matches to return (default 15, max 25)",
                    },
                },
                "required": ["title_query"],
                "additionalProperties": False,
            },
        },
    },
]
