import json
import requests
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_bookshelf(name: str, description: str = None, books: list = None, tags: list = None) -> str:
    """
    Creates a new bookshelf in Bookstack.

    This function supports two usage scenarios:
      1) Creating a bookshelf
      2) Retrieving the tool's metadata by passing name="__tool_info__"

    Args:
        name (str): The name of the bookshelf
        description (str, optional): A description of the bookshelf
        books (list, optional): A list of book IDs to include in the shelf
        tags (list, optional): A list of tag objects (each with 'name' and 'value')

    Returns:
        str: JSON-formatted string containing the response
    """
    if name == "__tool_info__":
        info = {
            "name": "create_bookshelf",
            "description": "Creates a new bookshelf in Bookstack",
            "args": {
                "name": {
                    "type": "string",
                    "description": "The name of the bookshelf",
                    "required": True
                },
                "description": {
                    "type": "string",
                    "description": "A description of the bookshelf",
                    "required": False
                },
                "books": {
                    "type": "list",
                    "description": "A list of book IDs to include in the shelf",
                    "required": False
                },
                "tags": {
                    "type": "list",
                    "description": "A list of tag objects (each with 'name' and 'value')",
                    "required": False
                }
            }
        }
        return json.dumps(info)

    if not name:
        return json.dumps({"error": "Bookshelf name is required"})

    base_url = os.environ.get("BS_URL", "https://knowledge.oculair.ca").rstrip("/")
    token_id = os.environ.get("BS_TOKEN_ID")
    token_secret = os.environ.get("BS_TOKEN_SECRET")

    if not token_id or not token_secret:
        return json.dumps({"error": "BS_TOKEN_ID and BS_TOKEN_SECRET environment variables must be set."})

    try:
        session = requests.Session()
        adapter = HTTPAdapter(max_retries=Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        ))
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        headers = {
            "Authorization": f"Token {token_id}:{token_secret}",
            "Content-Type": "application/json"
        }

        payload = {
            "name": name
        }
        if description:
            payload["description"] = description
        if books:
            payload["books"] = books
        if tags:
            payload["tags"] = tags

        response = session.post(
            f"{base_url}/api/shelves",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return json.dumps(response.json())
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Network or HTTP error - {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"Unexpected error - {str(e)}"})
    finally:
        session.close()

if __name__ == "__main__":
    print("Testing create_bookshelf tool...")
    
    # Set up environment with credentials
    os.environ["BS_URL"] = "https://knowledge.oculair.ca"
    os.environ["BS_TOKEN_ID"] = "POnHR9Lbvm73T2IOcyRSeAqpA8bSGdMT"
    os.environ["BS_TOKEN_SECRET"] = "735wM5dScfUkcOy7qcrgqQ1eC5fBF7IE"
    
    print("\nConfiguration:")
    print(f"API Base URL: {os.environ.get('BS_URL')}")
    print(f"Authorization header: Token {os.environ.get('BS_TOKEN_ID')}:{os.environ.get('BS_TOKEN_SECRET')[:10]}...")

    # Retrieve tool info
    print("\nTool Information:")
    tool_info = create_bookshelf("__tool_info__", "")
    print(json.dumps(json.loads(tool_info), indent=4))

    # Example bookshelf creation
    print("\nCreating test bookshelf...")
    try:
        new_shelf = create_bookshelf(
            name="Test Bookshelf",
            description="This is a test bookshelf created via the API",
            books=[7],  # Include our test book (ID: 7)
            tags=[{"name": "test", "value": "api"}]
        )
        response = json.loads(new_shelf)
        if "error" in response:
            print(f"Error creating bookshelf: {response['error']}")
        else:
            print("Bookshelf created successfully!")
            print(json.dumps(response, indent=2))
    except Exception as e:
        print(f"Error during test: {str(e)}")