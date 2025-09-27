Guide: Converting Python Tools to MCP Server
This guide provides detailed instructions on how to convert Python tools to work with the Model Context Protocol (MCP) system. By following these steps, you can create an MCP server that exposes Python tools to be used by AI assistants.

1. Setting Up the Directory Structure
Create the following directory structure for your Python MCP tools:

python_tools/
├── __init__.py           # Package initialization
├── requirements.txt      # Dependencies
├── .env.example          # Environment variables template
├── mcp_server.py         # Main MCP server
├── README.md             # Documentation
└── your_tool.py          # Your Python tool implementation
2. Creating a Python Tool
Each Python tool should follow this pattern:

import json

def your_tool_name(param1=default1, param2=default2, ...):
    """
    Description of what your tool does.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        str: JSON-formatted string containing the response
    """
    # Special case for tool info request
    if param1 == "__tool_info__":
        info = {
            "name": "your_tool_name",
            "description": "Description of what your tool does",
            "args": {
                "param1": {
                    "type": "string",  # or int, boolean, etc.
                    "description": "Description of param1",
                    "required": False  # True if required
                },
                "param2": {
                    "type": "int",
                    "description": "Description of param2",
                    "required": False
                }
            }
        }
        return json.dumps(info)
    
    # Validate parameters
    if not valid_param1(param1):
        return json.dumps({"error": "Invalid param1 value"})
    
    # Implement your tool logic here
    try:
        # Your code here
        result = {"key": "value", "data": [1, 2, 3]}
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": f"Error: {str(e)}"})
Key points:

The tool must accept a special __tool_info__ parameter to return metadata
Always return a JSON-formatted string
Include proper error handling
Document parameters and return values
3. Package Initialization
Create an __init__.py file to make your tools available as a package:

from .your_tool import your_tool_name

__all__ = ['your_tool_name']
4. MCP Server Implementation
Create an mcp_server.py file with the following structure:

#!/usr/bin/env python3
import os
import sys
import json
import uuid
import traceback
import threading
import time
from typing import Dict, Any, Callable
from queue import Queue, Empty
from flask import Flask, request, Response, jsonify
from flask_cors import CORS

# Import your tools
from python_tools import your_tool_name

# Dictionary of tools to register with the MCP
TOOLS = {
    "your_tool_name": your_tool_name
}

# Default port
DEFAULT_PORT = 3333

class McpServer:
    def __init__(self):
        # Initialize server state
        self.tools = TOOLS
        self.tool_info = {}
        self.clients = {}
        self.active_connections = {}
        self.is_connected = False
        self.start_time = time.time()
        
        # Load tool info
        for tool_name, tool_func in self.tools.items():
            try:
                info_json = tool_func("__tool_info__")
                self.tool_info[tool_name] = json.loads(info_json)
            except Exception as e:
                print(f"Error loading tool info for {tool_name}: {str(e)}", file=sys.stderr)
                self.tool_info[tool_name] = {
                    "name": tool_name,
                    "description": tool_func.__doc__ or "No description available",
                    "args": {}
                }
        
        # Create Flask app
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Register routes
        self.app.route('/sse', methods=['GET'])(self.connect_and_stream)
        self.app.route('/message', methods=['POST'])(self.handle_request)
        self.app.route('/health', methods=['GET'])(self.health_check)
        
        # Set up ping thread
        self.ping_interval = 30
        self.stop_ping = threading.Event()
        self.ping_thread = None
    
    def generate_client_id(self):
        return f"client_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    
    def connect_and_stream(self):
        # Handle SSE connection
        client_id = self.generate_client_id()
        client_ip = request.remote_addr
        
        # Set headers for SSE
        headers = {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
        
        # Create client queue and track connection
        self.clients[client_id] = Queue()
        self.active_connections[client_id] = {
            'ip': client_ip,
            'connected_at': time.time(),
            'last_ping': time.time()
        }
        
        self.is_connected = True
        
        # Start ping thread if needed
        if self.ping_thread is None or not self.ping_thread.is_alive():
            self.stop_ping.clear()
            self.ping_thread = threading.Thread(target=self.ping_clients)
            self.ping_thread.daemon = True
            self.ping_thread.start()
        
        # Generate SSE stream
        def generate():
            try:
                yield ': connected\n\n'
                
                while True:
                    try:
                        message = self.clients[client_id].get(timeout=30)
                        if message is None:
                            break
                        yield f"event: message\ndata: {json.dumps(message)}\n\n"
                    except Empty:
                        yield ": ping\n\n"
                        self.active_connections[client_id]['last_ping'] = time.time()
            except GeneratorExit:
                self.cleanup_connection(client_id)
        
        return Response(generate(), headers=headers)
    
    def handle_request(self):
        # Handle MCP request
        try:
            if not self.is_connected:
                return jsonify({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32000,
                        "message": "No active SSE connection"
                    },
                    "id": None
                }), 503
            
            data = request.json
            response = self._process_request(data)
            return jsonify(response)
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            return jsonify({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                },
                "id": None
            }), 500
    
    def _process_request(self, request):
        # Process MCP request
        try:
            method = request.get("method")
            
            if method == "list_tools":
                response = self._handle_list_tools(request)
            elif method == "call_tool":
                response = self._handle_call_tool(request)
            else:
                response = {
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            if "id" in request:
                response["id"] = request["id"]
            
            response["jsonrpc"] = "2.0"
            return response
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            if "id" in request:
                response["id"] = request["id"]
            return response
    
    def _handle_list_tools(self, request):
        # Return list of available tools
        tools = []
        for tool_name, info in self.tool_info.items():
            tools.append({
                "name": info["name"],
                "description": info["description"],
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        arg_name: {
                            "type": arg_info["type"],
                            "description": arg_info["description"]
                        }
                        for arg_name, arg_info in info.get("args", {}).items()
                    },
                    "required": [
                        arg_name
                        for arg_name, arg_info in info.get("args", {}).items()
                        if arg_info.get("required", False)
                    ]
                }
            })
        
        return {
            "result": {
                "tools": tools
            }
        }
    
    def _handle_call_tool(self, request):
        # Call the requested tool
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            return {
                "error": {
                    "code": -32602,
                    "message": "Invalid params: missing tool name"
                }
            }
        
        if tool_name not in self.tools:
            return {
                "error": {
                    "code": -32601,
                    "message": f"Tool not found: {tool_name}"
                }
            }
        
        tool_func = self.tools[tool_name]
        
        try:
            result = tool_func(**arguments)
            result_json = json.loads(result)
            
            if isinstance(result_json, dict) and "error" in result_json:
                return {
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": result_json["error"]
                            }
                        ],
                        "isError": True
                    }
                }
            
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result_json, indent=2)
                        }
                    ]
                }
            }
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            return {
                "error": {
                    "code": -32603,
                    "message": f"Error calling tool {tool_name}: {str(e)}"
                }
            }
    
    def run(self, host='0.0.0.0', port=None):
        port = port or int(os.environ.get('MCP_PORT', DEFAULT_PORT))
        
        print(f"MCP Python Server started with {len(self.tools)} tools:", file=sys.stderr)
        for tool_name in self.tools:
            print(f"  - {tool_name}", file=sys.stderr)
        
        print(f"Server running at http://{host}:{port}", file=sys.stderr)
        print(f"SSE endpoint: http://{host}:{port}/sse", file=sys.stderr)
        print(f"Message endpoint: http://{host}:{port}/message", file=sys.stderr)
        
        try:
            self.app.run(host=host, port=port, debug=False, threaded=True)
        except KeyboardInterrupt:
            print("Shutting down server...", file=sys.stderr)
            self.stop_ping.set()

def main():
    server = McpServer()
    server.run()

if __name__ == "__main__":
    main()
5. Dependencies
Create a requirements.txt file with the necessary dependencies:

requests>=2.25.0
python-dotenv>=0.15.0
flask>=2.0.0
flask-cors>=3.0.10
6. Environment Variables
Create a .env.example file for any required environment variables:

# API credentials
API_KEY=your_api_key_here
API_SECRET=your_api_secret_here

# Server configuration
MCP_PORT=3333
7. MCP Configuration
Add your Python MCP server to the MCP settings file:

Locate your MCP settings file:

For Roo-Cline: c:\Users\<username>\AppData\Roaming\Code\User\globalStorage\rooveterinaryinc.roo-cline\settings\cline_mcp_settings.json
For Claude Desktop: ~/Library/Application Support/Claude/claude_desktop_config.json (macOS)
Add your server configuration:

{
  "mcpServers": {
    "your_python_server": {
      "url": "http://localhost:3333/sse",
      "disabled": false,
      "alwaysAllow": [],
      "env": {
        "API_KEY": "your_api_key",
        "API_SECRET": "your_api_secret"
      }
    }
  }
}
8. Running the Server
Start your MCP server:

python mcp_server.py
The server will start and listen on the specified port (default: 3333).

9. Testing
Test your tool using the MCP system:

<use_mcp_tool>
<server_name>your_python_server</server_name>
<tool_name>your_tool_name</tool_name>
<arguments>
{
  "param1": "value1",
  "param2": 42
}
</arguments>
</use_mcp_tool>
10. Troubleshooting
If your tool isn't working:

Check the server logs for errors
Verify the tool is properly registered in the TOOLS dictionary
Ensure your tool returns valid JSON
Check that the MCP settings file has the correct URL
Verify the server is running and accessible at the specified URL
Check that any required environment variables are set
By following these steps, you can convert any Python tool to work with the MCP system, allowing AI assistants to use your custom functionality.