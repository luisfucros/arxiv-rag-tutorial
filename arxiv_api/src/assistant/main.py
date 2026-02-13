import json
import logging

from openai import OpenAI
from services.search import SearchEngineService

from .prompts import SYSTEM_PROMPT
from .tools import SEARCH_TOOL

logger = logging.getLogger(__name__)


class ArxivAssistant:
    def __init__(self,
                 search_engine: SearchEngineService,
                 client: OpenAI,
                 model: str = "gpt-4.1-nano-2025-04-14"):
        self.client = client
        self.model = model
        self.search_engine = search_engine
        self.tools = SEARCH_TOOL

    def chat(self, chat_history: list) -> str:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ] + chat_history

        # First pass: model decides whether to call a tool
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tools,
        )

        assistant_message = response.choices[0].message
        if assistant_message.tool_calls is None:
            return assistant_message.content

        messages.append(assistant_message)

        # Execute tool calls
        for tool_call in assistant_message.tool_calls or []:
            if tool_call.function.name == "search_arxiv":
                args = json.loads(tool_call.function.arguments)

                print(args)  # Debugging line to inspect arguments

                results = self.search_engine.search(
                    query=args["query"],
                    top_k=10
                    # filters=args.get("filters"),
                )

                print(results)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(results),
                    }
                )

        # Second pass: model uses tool results to answer
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tools,
        )
        return response.choices[0].message.content
