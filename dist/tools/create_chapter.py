import json
import requests
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_chapter(book_id: int, name: str, description: str = None, tags: list = None, priority: int = None) -> str:
    """
    Creates a new chapter in Bookstack.

    This function supports two usage scenarios:
      1) Creating a chapter
      2) Retrieving the tool's metadata by passing name="__tool_info__"

    Args:
        book_id (int): The ID of the book to create the chapter in.
        name (str): The name of the chapter.
        description (str, optional): A description of the chapter. Defaults to None.
        tags (list, optional): A list of tag objects (each with 'name' and 'value'). Defaults to None.
        priority (int, optional): Chapter priority. Defaults to None.

    Returns:
        str: JSON-formatted string containing the response
    """
    if name == "__tool_info__":
        info = {
            "name": "create_chapter",
            "description": "Creates a new chapter in Bookstack",
            "args": {
                "book_id": {
                    "type": "int",
                    "description": "The ID of the book to create the chapter in",
                    "required": True
                },
                "name": {
                    "type": "string",
                    "description": "The name of the chapter",
                    "required": True
                },
                "description": {
                    "type": "string",
                    "description": "A description of the chapter",
                    "required": False
                },
                "tags": {
                    "type": "list",
                    "description": "A list of tag objects (each with 'name' and 'value')",
                    "required": False
                },
                "priority": {
                    "type": "int",
                    "description": "Chapter priority",
                    "required": False
                }
            }
        }
        return json.dumps(info)

    if not isinstance(book_id, int) or book_id <= 0:
        return json.dumps({"error": "Valid book ID is required"})
    if not name:
        return json.dumps({"error": "Chapter name is required"})

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
            "book_id": book_id,
            "name": name
        }
        if description:
            payload["description"] = description
        if tags:
            payload["tags"] = tags
        if priority is not None:
            payload["priority"] = priority

        response = session.post(
            f"{base_url}/api/chapters",
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
    print("Testing create_chapter tool...")
    
    # Set up environment with credentials
    os.environ["BS_URL"] = "https://knowledge.oculair.ca"
    os.environ["BS_TOKEN_ID"] = "POnHR9Lbvm73T2IOcyRSeAqpA8bSGdMT"
    os.environ["BS_TOKEN_SECRET"] = "735wM5dScfUkcOy7qcrgqQ1eC5fBF7IE"
    
    print("\nConfiguration:")
    print(f"API Base URL: {os.environ.get('BS_URL')}")
    print(f"Authorization header: Token {os.environ.get('BS_TOKEN_ID')}:{os.environ.get('BS_TOKEN_SECRET')[:10]}...")

    # Retrieve tool info
    print("\nTool Information:")
    tool_info = create_chapter("__tool_info__", 0, "")
    print(json.dumps(json.loads(tool_info), indent=4))

    # Example chapter creation
    print("\nCreating test chapter...")
    try:
        # Assuming a book with ID 1 exists
        new_chapter = create_chapter(
            book_id=1,
            name="My Test Chapter",
            description="This is a test chapter created via the API.",
            tags=[{"name": "Test", "value": "API"}]
        )
        response = json.loads(new_chapter)
        if "error" in response:
            print(f"\nError creating chapter: {response['error']}")
        else:
            print("\nChapter created successfully!")
            print(json.dumps(response, indent=2))
    except Exception as e:
        print(f"\nError during test: {str(e)}")