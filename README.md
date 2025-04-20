# Saaro Search MCP Server

A Model Context Protocol (MCP) server that provides access to the Brave Search API, running as a background thread.

## Features

- Runs as a background thread
- Implements JSON-RPC 2.0 protocol
- Rate limiting support
- Brave Search API integration

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -e .
```

3. Set up your Brave Search API key:
   - Get an API key from [Brave Search API](https://brave.com/search/api/)
   - Create a `.env` file in the project root:
     ```
     BRAVE_API_KEY=your_api_key_here
     ```

## Usage

The server communicates via stdin/stdout using the JSON-RPC 2.0 protocol. Here are example requests:

1. List available tools:
```json
{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "listTools",
    "params": {}
}
```

2. Perform a web search:
```json
{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "callTool",
    "params": {
        "name": "brave_web_search",
        "arguments": {
            "query": "your search query",
            "count": 10
        }
    }
}
```

To run the server:
```bash
python main.py
```

## Development

The server is implemented as a Python thread, making it suitable for integration into larger applications. The main components are:

- `MCPServer`: The main server class that runs in a background thread
- `BraveSearchConfig`: Configuration class for API settings
- Request/response queues for thread-safe communication