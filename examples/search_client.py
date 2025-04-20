from queue import Queue
import json
import os
import threading
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from brave_search.server import MCPServer, BraveSearchConfig

class SearchClient:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Get API key from environment
        api_key = os.getenv("BRAVE_API_KEY")
        if not api_key:
            raise ValueError("BRAVE_API_KEY environment variable is required")
        
        # Configure and start server
        config = BraveSearchConfig(api_key=api_key)
        self.server = MCPServer(config)
        self.server.start()
        
        # Request counter for generating unique IDs
        self._request_counter = 0
        self._counter_lock = threading.Lock()
    
    def _get_request_id(self) -> int:
        with self._counter_lock:
            self._request_counter += 1
            return self._request_counter
    
    def search(self, query: str, count: int = 10) -> Dict[str, Any]:
        """
        Perform a web search using the Brave Search API.
        
        Args:
            query: The search query
            count: Number of results to return (max 20)
            
        Returns:
            Dict containing the search results or error information
        """
        request = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": "callTool",
            "params": {
                "name": "brave_web_search",
                "arguments": {
                    "query": query,
                    "count": count
                }
            }
        }
        
        # Send request to server
        self.server.request_queue.put(request)
        
        # Wait for and return response
        response = self.server.response_queue.get()
        return response
    
    def close(self):
        """Stop the server thread and clean up"""
        if self.server.is_alive():
            self.server.stop()

# Example usage
if __name__ == "__main__":
    # Create client
    client = SearchClient()
    
    try:
        # Perform a search
        response = client.search("Python programming")
        
        # Check for errors
        if "error" in response:
            print(f"Error: {response['error']['message']}")
        else:
            # Process results
            content = response["result"]["content"][0]["text"]
            print("Search Results:")
            print(content)
            
    finally:
        # Clean up
        client.close()
