SEARCH_TOOL = [
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
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    }
]
