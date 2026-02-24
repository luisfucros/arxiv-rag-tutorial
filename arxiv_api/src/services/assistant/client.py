import json
import logging
from typing import Any, Dict, Generator, List, Optional
from uuid import UUID

from arxiv_lib.repositories.paper import PaperRepository
from openai import OpenAI
from repositories.chat_history import ChatRepository
from services.cache import CacheClient
from services.search import SearchEngineService
from utils import paper_to_dict

from .prompts import SYSTEM_PROMPT
from .tools import TOOLS

logger = logging.getLogger(__name__)


class ArxivAssistant:
    DEFAULT_MODEL = "gpt-4.1-nano-2025-04-14"

    def __init__(
        self,
        search_engine: SearchEngineService,
        chat_repo: ChatRepository,
        paper_repo: PaperRepository,
        client: OpenAI,
        cache: Optional[CacheClient] = None,
        model: str = DEFAULT_MODEL,
        top_k: int = 10,
    ) -> None:
        self.client = client
        self.model = model
        self.paper_repo = paper_repo
        self.chat_repo = chat_repo
        self.search_engine = search_engine
        self.cache = cache
        self.top_k = top_k
        self.tools = TOOLS

        self._tool_handlers = {
            "search_arxiv": self._handle_search_arxiv,
            "get_by_arxiv_id": self._handle_get_by_arxiv_id,
        }

    def chat_stream(
        self,
        chat_history: List[Dict[str, Any]],
        user_id: int,
        session_id: UUID,
        max_rounds: int = 5,
    ) -> Generator[str, None, None]:
        """
        Streaming ReAct loop.
        Streams tokens only when the model produces final content.
        Tool calls are executed internally (not streamed).
        """

        if self.chat_repo.get_session(session_id, user_id) is None:
            self.chat_repo.create_session(user_id, session_id)

        user_query = chat_history[-1]["content"]

        if self.cache:
            cached_response = None
            try:
                cached_response = self.cache.find_cached_response(user_query)
                if cached_response:
                    logger.info("Returning cached response for exact query match")
                    yield cached_response.get("response")
                    return
            except Exception as e:
                logger.warning(f"Cache check failed, proceeding with normal flow: {e}")

        self.chat_repo.create_message(session_id, "user", user_query)
        messages = self._build_messages(chat_history)

        for _ in range(max_rounds):
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                stream=True,
            )

            assistant_message = {"role": "assistant", "content": "", "tool_calls": []}
            tool_calls_by_index = {}

            for chunk in stream:
                delta = chunk.choices[0].delta

                # Stream content tokens immediately
                if delta.content:
                    assistant_message["content"] += delta.content
                    yield delta.content

                # Collect tool calls (do not stream)
                if delta.tool_calls:
                    for tool_call_delta in delta.tool_calls:
                        index = tool_call_delta.index

                        if index not in tool_calls_by_index:
                            tool_calls_by_index[index] = {
                                "id": tool_call_delta.id,
                                "type": "function",
                                "function": {
                                    "name": "",
                                    "arguments": "",
                                },
                            }

                        tool_call = tool_calls_by_index[index]

                        if tool_call_delta.function:
                            if tool_call_delta.function.name:
                                tool_call["function"]["name"] = tool_call_delta.function.name

                            if tool_call_delta.function.arguments:
                                tool_call["function"]["arguments"] += (
                                    tool_call_delta.function.arguments
                                )

            collected_tool_calls = list(tool_calls_by_index.values())
            # If no tool calls → done streaming
            if not collected_tool_calls:
                self.chat_repo.create_message(session_id, "assistant", assistant_message["content"])
                if self.cache:
                    try:
                        self.cache.store_response(user_query, assistant_message["content"])
                    except Exception as e:
                        logger.warning(f"Failed to store response in cache: {e}")

                return

            # Append assistant message
            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_message["content"],
                    "tool_calls": collected_tool_calls,
                }
            )

            # Execute tools
            self._execute_tool_calls_streaming(collected_tool_calls, messages, user_id)

        # Safety fallback (non-streamed final response)
        response = self._create_completion(messages)
        final_response = response.choices[0].message.content or ""
        self.chat_repo.create_message(session_id, "assistant", final_response)
        if self.cache:
            try:
                self.cache.store_response(user_query, final_response)
            except Exception as e:
                logger.warning(f"Failed to store response in cache: {e}")
        yield final_response

    def chat(
        self,
        chat_history: List[Dict[str, Any]],
        user_id: int,
        session_id: UUID,
        max_rounds: int = 5,
    ) -> str:
        """
        Executes a ReAct-style loop:
        - If no tool call → return immediately
        - If tool call → execute and continue reasoning
        """

        if self.chat_repo.get_session(session_id, user_id) is None:
            self.chat_repo.create_session(user_id, session_id)

        user_query = chat_history[-1]["content"]

        if self.cache:
            cached_response = None
            try:
                cached_response = self.cache.find_cached_response(user_query)
                if cached_response:
                    logger.info("Returning cached response for exact query match")
                    return cached_response.get("response")
            except Exception as e:
                logger.warning(f"Cache check failed, proceeding with normal flow: {e}")

        self.chat_repo.create_message(session_id, "user", user_query)
        messages = self._build_messages(chat_history)

        for _ in range(max_rounds):
            response = self._create_completion(messages)
            assistant_message = response.choices[0].message

            messages.append(assistant_message)

            if not assistant_message.tool_calls:
                self.chat_repo.create_message(
                    session_id, "assistant", assistant_message.content or ""
                )
                if self.cache:
                    try:
                        self.cache.store_response(user_query, assistant_message.content or "")
                    except Exception as e:
                        logger.warning(f"Failed to store response in cache: {e}")
                return assistant_message.content or ""

            self._execute_tool_calls(assistant_message.tool_calls, messages, user_id=user_id)

        # Safety fallback (if max rounds reached)
        response = self._create_completion(messages)
        final_response = response.choices[0].message.content or ""
        self.chat_repo.create_message(session_id, "assistant", final_response)
        if self.cache:
            try:
                self.cache.store_response(user_query, final_response)
            except Exception as e:
                logger.warning(f"Failed to store response in cache: {e}")
        return final_response

    def _build_messages(self, chat_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [{"role": "system", "content": SYSTEM_PROMPT}, *chat_history]

    def _create_completion(self, messages: List[Dict[str, Any]]):
        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tools,
        )

    def _execute_tool_calls(
        self, tool_calls: List[Any], messages: List[Dict[str, Any]], user_id: int
    ) -> None:
        for tool_call in tool_calls:
            handler = self._tool_handlers.get(tool_call.function.name)

            if not handler:
                logger.warning("Unknown tool call received: %s", tool_call.function.name)
                continue

            try:
                arguments = self._parse_arguments(tool_call.function.arguments)
                result = handler(arguments, user_id=user_id)
            except Exception as exc:
                logger.exception("Tool execution failed: %s", tool_call.function.name)
                result = {"error": str(exc)}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )

    def _execute_tool_calls_streaming(
        self, tool_calls: List[Any], messages: List[Dict[str, Any]], user_id: int
    ) -> None:
        for tool_call in tool_calls:
            handler = self._tool_handlers.get(tool_call["function"]["name"])

            if not handler:
                logger.warning("Unknown tool call received: %s", tool_call["function"]["name"])
                continue

            try:
                arguments = self._parse_arguments(tool_call["function"]["arguments"])
                result = handler(arguments, user_id=user_id)
            except Exception as exc:
                logger.exception("Tool execution failed: %s", tool_call["function"]["name"])
                result = {"error": str(exc)}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(result),
                }
            )

    def _parse_arguments(self, raw_args: str) -> Dict[str, Any]:
        try:
            return json.loads(raw_args)
        except json.JSONDecodeError as exc:
            logger.error("Invalid JSON tool arguments: %s", raw_args)
            raise ValueError("Invalid tool arguments") from exc

    def _handle_search_arxiv(self, args: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        query = args.get("query")
        arxiv_id = args.get("arxiv_id")
        print(f"query: {query}")
        print(f"arxiv_id: {args.get('arxiv_id')}")
        if not query:
            raise ValueError("Missing 'query' parameter")

        logger.info("Executing search_arxiv | query=%s", query)

        results = self.search_engine.search(
            query=query,
            top_k=args.get("top_k", self.top_k),
            filters={"arxiv_id": arxiv_id} if arxiv_id is not None else None,
            user_id=user_id,
        )

        return {"results": results}

    def _handle_get_by_arxiv_id(self, args: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        arxiv_id = args.get("arxiv_id")
        print(f"arxiv_id: {arxiv_id}")
        if not arxiv_id:
            raise ValueError("Missing 'arxiv_id' parameter")

        logger.info("Fetching paper | arxiv_id=%s", arxiv_id)

        paper = self.paper_repo.get_by_arxiv_id(arxiv_id=arxiv_id)

        return {"paper": paper_to_dict(paper) if paper is not None else None}
