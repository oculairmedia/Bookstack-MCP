import json
import requests
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_book(name: str, description: str, tags: list = None, image_id: int = None) -> str:
    """
    Creates a new book in Bookstack.

    This function supports two usage scenarios:
      1) Creating a book
      2) Retrieving the tool's metadata by passing name="__tool_info__"

    Args:
        name (str): The name of the book
        description (str): A description of the book
        tags (list, optional): A list of tag objects (each with 'name' and 'value')
        image_id (int, optional): The ID of an image to use as the cover

    Returns:
        str: JSON-formatted string containing the response
    """
    if name == "__tool_info__":
        info = {
            "name": "create_book",
            "description": "Creates a new book in Bookstack",
            "args": {
                "name": {
                    "type": "string",
                    "description": "The name of the book",
                    "required": True
                },
                "description": {
                    "type": "string",
                    "description": "A description of the book",
                    "required": True
                },
                "tags": {
                    "type": "list",
                    "description": "A list of tag objects (each with 'name' and 'value')",
                    "required": False
                },
                "image_id": {
                    "type": "int",
                    "description": "The ID of an image to use as the cover",
                    "required": False
                }
            }
        }
        return json.dumps(info)

    if not name or not description:
        return json.dumps({"error": "Name and description are required"})

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
            "name": name,
            "description": description
        }
        if tags:
            payload["tags"] = tags
        if image_id:
            payload["image_id"] = image_id

        response = session.post(
            f"{base_url}/api/books",
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
    print("Testing create_book tool...")
    
    # Set up environment with credentials
    os.environ["BS_URL"] = "https://knowledge.oculair.ca"
    os.environ["BS_TOKEN_ID"] = "POnHR9Lbvm73T2IOcyRSeAqpA8bSGdMT"
    os.environ["BS_TOKEN_SECRET"] = "735wM5dScfUkcOy7qcrgqQ1eC5fBF7IE"
    
    print("\nConfiguration:")
    print(f"API Base URL: {os.environ.get('BS_URL')}")
    print(f"Authorization header: Token {os.environ.get('BS_TOKEN_ID')}:{os.environ.get('BS_TOKEN_SECRET')[:10]}...")

    # Retrieve tool info
    print("\nTool Information:")
    tool_info = create_book("__tool_info__", "")
    print(json.dumps(json.loads(tool_info), indent=4))

    # Example book creation
    print("\nCreating test book...")
    try:
        new_book = create_book(
            "Test Book",
            "This is a test book created via the API",
            tags=[{"name": "test", "value": "api"}]
        )
        response = json.loads(new_book)
        if "error" in response:
            print(f"Error creating book: {response['error']}")
        else:
            print("Book created successfully!")
            print(json.dumps(response, indent=2))
    except Exception as e:
        print(f"Error during test: {str(e)}")