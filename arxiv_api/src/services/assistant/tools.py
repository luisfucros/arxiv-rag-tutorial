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
]
