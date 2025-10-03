#!/usr/bin/env python3
"""Read book 39 using bookstack_manage_content tool."""

import asyncio
import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

from fastmcp import FastMCP
from fastmcp_server.bookstack import register_bookstack_tools


async def main():
    """Read book 39."""
    mcp = FastMCP("BookStack Reader")
    register_bookstack_tools(mcp)
    
    tool = await mcp.get_tool("bookstack_manage_content")
    
    print("Reading book ID 39...")
    print("=" * 80)
    
    result = await tool.run({
        "operation": "read",
        "entity_type": "book",
        "id": 39
    })
    
    data = json.loads(result.content[0].text)
    
    if data.get("success"):
        book = data.get("data", {})
        print(f"\n📚 Book Details:")
        print(f"   ID: {book.get('id')}")
        print(f"   Name: {book.get('name')}")
        print(f"   Slug: {book.get('slug')}")
        print(f"   Description: {book.get('description')}")
        print(f"   Created: {book.get('created_at')}")
        print(f"   Updated: {book.get('updated_at')}")
        print(f"   Created by: {book.get('created_by')}")
        print(f"   Owned by: {book.get('owned_by')}")
        
        if book.get('tags'):
            print(f"\n   Tags:")
            for tag in book['tags']:
                print(f"      - {tag.get('name')}: {tag.get('value')}")
        
        print(f"\n✅ Successfully read book 39!")
    else:
        print(f"❌ Error: {data}")


if __name__ == "__main__":
    asyncio.run(main())

