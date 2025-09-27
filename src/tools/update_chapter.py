import json
import requests
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def update_chapter(id: int, book_id: int = None, name: str = None, description: str = None, tags: list = None, priority: int = None) -> str:
    """
    Updates a chapter in Bookstack.

    This function supports two usage scenarios:
      1) Updating a chapter
      2) Retrieving the tool's metadata by passing id="__tool_info__"

    Args:
        id (int): The ID of the chapter to update
        book_id (int, optional): The ID of the book to move the chapter to
        name (str, optional): The new name of the chapter
        description (str, optional): A new description of the chapter
        tags (list, optional): A new list of tag objects (each with 'name' and 'value')
        priority (int, optional): New chapter priority

    Returns:
        str: JSON-formatted string containing the response
    """
    if id == "__tool_info__":
        info = {
            "name": "update_chapter",
            "description": "Updates a chapter in Bookstack",
            "args": {
                "id": {
                    "type": "int",
                    "description": "The ID of the chapter to update",
                    "required": True
                },
                "book_id": {
                    "type": "int",
                    "description": "The ID of the book to move the chapter to",
                    "required": False
                },
                "name": {
                    "type": "string",
                    "description": "The new name of the chapter",
                    "required": False
                },
                "description": {
                    "type": "string",
                    "description": "A new description of the chapter",
                    "required": False
                },
                "tags": {
                    "type": "list",
                    "description": "A new list of tag objects (each with 'name' and 'value')",
                    "required": False
                },
                "priority": {
                    "type": "int",
                    "description": "New chapter priority",
                    "required": False
                }
            }
        }
        return json.dumps(info)

    if not isinstance(id, int) or id <= 0:
        return json.dumps({"error": "Valid chapter ID is required"})
    if not any([book_id, name, description, tags, priority]):
        return json.dumps({"error": "At least one field to update must be provided"})

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

        # Get current chapter data first
        try:
            current_chapter = session.get(
                f"{base_url}/api/chapters/{id}",
                headers=headers,
                timeout=30
            )
            current_chapter.raise_for_status()
            current_data = current_chapter.json()
        except requests.exceptions.RequestException as e:
            return json.dumps({"error": f"Failed to retrieve current chapter data - {str(e)}"})

        # Prepare update payload with current values as defaults
        payload = {
            "book_id": book_id if book_id is not None else current_data.get("book_id"),
            "name": name if name is not None else current_data.get("name", ""),
            "description": description if description is not None else current_data.get("description", "")
        }
        if tags is not None:
            payload["tags"] = tags
        if priority is not None:
            payload["priority"] = priority

        response = session.put(
            f"{base_url}/api/chapters/{id}",
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
    print("Testing update_chapter tool...")
    
    # Set up environment with credentials
    os.environ["BS_URL"] = "https://knowledge.oculair.ca"
    os.environ["BS_TOKEN_ID"] = "POnHR9Lbvm73T2IOcyRSeAqpA8bSGdMT"
    os.environ["BS_TOKEN_SECRET"] = "735wM5dScfUkcOy7qcrgqQ1eC5fBF7IE"
    
    print("\nConfiguration:")
    print(f"API Base URL: {os.environ.get('BS_URL')}")
    print(f"Authorization header: Token {os.environ.get('BS_TOKEN_ID')}:{os.environ.get('BS_TOKEN_SECRET')[:10]}...")

    # Retrieve tool info
    print("\nTool Information:")
    tool_info = update_chapter("__tool_info__", 0)
    print(json.dumps(json.loads(tool_info), indent=4))

    # Example chapter update
    print("\nUpdating test chapter (ID: 2)...")
    try:
        updated_chapter = update_chapter(
            2,  # Update our test chapter
            name="Updated Test Chapter",
            description="This chapter has been updated via the API.",
            tags=[{"name": "updated", "value": "true"}]
        )
        response = json.loads(updated_chapter)
        if "error" in response:
            print(f"Error updating chapter: {response['error']}")
        else:
            print("Chapter updated successfully!")
            print(json.dumps(response, indent=2))
    except Exception as e:
        print(f"Error during test: {str(e)}")