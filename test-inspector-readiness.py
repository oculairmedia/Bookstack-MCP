#!/usr/bin/env python3
"""
Test script to verify the BookStack FastMCP server is ready for MCP Inspector validation.

This script performs pre-flight checks before running the MCP Inspector.
"""

import os
import sys
import json
from pathlib import Path


def check_environment():
    """Check if required environment variables are set."""
    print("🔍 Checking environment variables...")
    
    required_vars = ["BS_URL", "BS_TOKEN_ID", "BS_TOKEN_SECRET"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("\n💡 Please set them in Bookstack-MCP/.env file:")
        print("   BS_URL=https://your-bookstack.example.com")
        print("   BS_TOKEN_ID=your_token_id")
        print("   BS_TOKEN_SECRET=your_token_secret")
        return False
    
    print("✅ All required environment variables are set")
    print(f"   BS_URL: {os.getenv('BS_URL')}")
    print(f"   BS_TOKEN_ID: {os.getenv('BS_TOKEN_ID')[:10]}...")
    return True


def check_dependencies():
    """Check if required Python packages are installed."""
    print("\n🔍 Checking Python dependencies...")
    
    required_packages = {
        "fastmcp": "FastMCP",
        "requests": "Requests",
        "pydantic": "Pydantic"
    }
    
    missing_packages = []
    
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"✅ {name} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {name} is NOT installed")
    
    if missing_packages:
        print(f"\n💡 Install missing packages:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True


def check_server_module():
    """Check if the FastMCP server module can be imported."""
    print("\n🔍 Checking FastMCP server module...")

    try:
        # Add fastmcp_server to path
        server_path = Path(__file__).parent / "fastmcp_server"
        sys.path.insert(0, str(server_path.parent))

        from fastmcp_server.bookstack import register_bookstack_tools
        from fastmcp import FastMCP

        print("✅ FastMCP server module can be imported")

        # Try to create a server instance
        mcp = FastMCP("Test Server")
        register_bookstack_tools(mcp)

        # Count registered tools by checking the mcp instance
        print(f"✅ Server tools registered successfully")
        print(f"   Tools are available via the FastMCP server")

        return True

    except Exception as e:
        print(f"❌ Failed to import server module: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_bookstack_connection():
    """Test connection to BookStack API."""
    print("\n🔍 Testing BookStack API connection...")
    
    bs_url = os.getenv("BS_URL")
    bs_token_id = os.getenv("BS_TOKEN_ID")
    bs_token_secret = os.getenv("BS_TOKEN_SECRET")
    
    if not all([bs_url, bs_token_id, bs_token_secret]):
        print("⚠️  Skipping connection test (missing credentials)")
        return True
    
    try:
        import requests
        
        headers = {
            "Authorization": f"Token {bs_token_id}:{bs_token_secret}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{bs_url}/api/books", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Successfully connected to BookStack")
            print(f"   Found {data.get('total', 0)} books")
            return True
        else:
            print(f"❌ BookStack API returned status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to connect to BookStack: {e}")
        return False


def print_inspector_commands():
    """Print commands to run the MCP Inspector."""
    print("\n" + "="*70)
    print("🎉 Pre-flight checks complete!")
    print("="*70)
    print("\n📋 Next steps to validate with MCP Inspector:\n")
    
    print("Option 1: Using stdio transport (recommended)")
    print("-" * 70)
    print("cd Bookstack-MCP/fastmcp_server")
    print("npx @modelcontextprotocol/inspector python run_stdio.py")
    
    print("\n\nOption 2: Using HTTP transport")
    print("-" * 70)
    print("# Terminal 1: Start the server")
    print("cd Bookstack-MCP/fastmcp_server")
    print("python -m fastmcp_server.my_server")
    print("\n# Terminal 2: Run the Inspector")
    print("npx @modelcontextprotocol/inspector")
    print("# Then connect to: http://localhost:3054/mcp/v1")
    
    print("\n\n📖 For detailed validation steps, see:")
    print("   Bookstack-MCP/MCP-INSPECTOR-VALIDATION.md")
    print("\n" + "="*70 + "\n")


def main():
    """Run all pre-flight checks."""
    print("="*70)
    print("BookStack FastMCP Server - MCP Inspector Readiness Check")
    print("="*70)

    # Load .env file if it exists
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print(f"\n📄 Loading environment from: {env_file}")
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
        except ImportError:
            print("⚠️  python-dotenv not installed, loading .env manually")
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
    
    checks = [
        ("Environment Variables", check_environment),
        ("Python Dependencies", check_dependencies),
        ("Server Module", check_server_module),
        ("BookStack Connection", check_bookstack_connection),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {name} check failed with error: {e}")
            results.append(False)
    
    print("\n" + "="*70)
    print("Summary")
    print("="*70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if all(results):
        print_inspector_commands()
        return 0
    else:
        print("\n⚠️  Please fix the failed checks before running MCP Inspector")
        return 1


if __name__ == "__main__":
    sys.exit(main())

