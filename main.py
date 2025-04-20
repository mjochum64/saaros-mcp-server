#!/usr/bin/env python3
import json
import os
import sys
try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv package is required. Please install it using:")
    print("pip install python-dotenv")
    sys.exit(1)

try:
    from brave_search.server import MCPServer, BraveSearchConfig
except ImportError:
    print("Error: Could not import server components. Please ensure the package is installed:")
    print("pip install -e .")
    sys.exit(1)

def main():
    # Load environment variables
    load_dotenv()
    
    # Check for API key
    api_key = os.getenv("BRAVE_API_KEY")
    if not api_key:
        print("Error: BRAVE_API_KEY environment variable is required", file=sys.stderr)
        print("Please create a .env file with your Brave Search API key:", file=sys.stderr)
        print("BRAVE_API_KEY=your_api_key_here", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Configure and start server
        config = BraveSearchConfig(api_key=api_key)
        server = MCPServer(config)
        server.start()
        
        print("Brave Search MCP Server running on stdio", file=sys.stderr)
        
        while True:
            try:
                # Read request from stdin
                request_line = sys.stdin.readline()
                if not request_line:
                    break
                
                request = json.loads(request_line)
                server.request_queue.put(request)
                
                # Wait for and write response
                response = server.response_queue.get()
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
                }
                print(json.dumps(error_response), flush=True)
                
    except KeyboardInterrupt:
        print("\nShutting down server...", file=sys.stderr)
    except Exception as e:
        print(f"Fatal error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    finally:
        server.stop()

if __name__ == "__main__":
    main()
