import threading
from queue import Queue, Empty
from typing import Any, Dict

try:
    import requests
    from pydantic import BaseModel
except ImportError as e:
    raise ImportError(
        "Required dependencies not found. Please install them using:\n"
        "pip install requests pydantic"
    ) from e

class BraveAPIError(Exception):
    """Custom exception for Brave API errors"""
    def __init__(self, message: str, request_id: Any = None):
        super().__init__(message)
        self.request_id = request_id

class BraveSearchConfig(BaseModel):
    api_key: str
    rate_limit_per_second: int = 1
    rate_limit_per_month: int = 15000

class MCPServer(threading.Thread):
    def __init__(self, config: BraveSearchConfig):
        super().__init__()
        self.config = config
        self.request_queue: Queue[Dict[str, Any]] = Queue()
        self.response_queue: Queue[Dict[str, Any]] = Queue()
        self.running = True
        
        # Rate limiting
        self._request_count = {"second": 0, "month": 0}
        self._last_reset = 0
    
    def run(self):
        while self.running:
            try:
                request = self.request_queue.get(timeout=1.0)
                if request:
                    response = self._handle_request(request)
                    self.response_queue.put(response)
            except Empty:
                continue
            except BraveAPIError as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": e.request_id,
                    "error": {"code": -32000, "message": str(e)}
                }
                self.response_queue.put(error_response)
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32603, "message": "Internal error"}
                }
                self.response_queue.put(error_response)

    def stop(self):
        self.running = False
        self.join()

    def _handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        method = request.get("method")
        request_id = request.get("id")
        
        try:
            if method == "listTools":
                return self._handle_list_tools(request_id)
            elif method == "callTool":
                return self._handle_call_tool(request_id, request.get("params", {}))
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Method {method} not found"}
                }
        except BraveAPIError as e:
            e.request_id = request_id
            raise

    def _handle_list_tools(self, request_id: Any) -> Dict[str, Any]:
        tools = [{
            "name": "brave_web_search",
            "description": "Performs a web search using the Brave Search API",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (max 400 chars, 50 words)"
                    },
                    "count": {
                        "type": "number",
                        "description": "Number of results (1-20, default 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        }]
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": tools}
        }

    def _handle_call_tool(self, request_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "brave_web_search":
            try:
                results = self._perform_web_search(
                    query=arguments["query"],
                    count=arguments.get("count", 10)
                )
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": results}],
                        "isError": False
                    }
                }
            except (KeyError, ValueError) as e:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32602, "message": f"Invalid params: {str(e)}"}
                }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Tool {tool_name} not found"}
            }

    def _perform_web_search(self, query: str, count: int = 10) -> str:
        url = 'https://api.search.brave.com/res/v1/web/search'
        headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip',
            'X-Subscription-Token': self.config.api_key
        }
        
        params = {
            'q': query,
            'count': min(count, 20)
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            if not response.ok:
                raise BraveAPIError(f"Brave API error: {response.status_code} {response.text}")

            data = response.json()
            results = []
            
            for result in data.get('web', {}).get('results', []):
                results.append(
                    f"Title: {result.get('title', '')}\n"
                    f"Description: {result.get('description', '')}\n"
                    f"URL: {result.get('url', '')}"
                )

            return "\n\n".join(results) if results else "No results found"
        except requests.Timeout as exc:
            raise BraveAPIError("Request timed out after 30 seconds") from exc
        except requests.RequestException as exc:
            raise BraveAPIError(f"Network error: {str(exc)}") from exc