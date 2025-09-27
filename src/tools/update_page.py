import json
import requests
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def update_page(id: int, book_id: int = None, chapter_id: int = None, name: str = None, markdown: str = None, html: str = None, tags: list = None, priority: int = None) -> str:
    """
    Updates a page in Bookstack.

    This function supports two usage scenarios:
      1) Updating a page
      2) Retrieving the tool's metadata by passing id="__tool_info__"

    Args:
        id (int): The ID of the page to update
        book_id (int, optional): The ID of the book to move the page to
        chapter_id (int, optional): The ID of the chapter to move the page to
        name (str, optional): The new name of the page
        markdown (str, optional): The new page content in Markdown format
        html (str, optional): The new page content in HTML format
        tags (list, optional): A new list of tag objects (each with 'name' and 'value')
        priority (int, optional): New page priority

    Returns:
        str: JSON-formatted string containing the response
    """
    if id == "__tool_info__":
        info = {
            "name": "update_page",
            "description": "Updates a page in Bookstack",
            "args": {
                "id": {
                    "type": "int",
                    "description": "The ID of the page to update",
                    "required": True
                },
                "book_id": {
                    "type": "int",
                    "description": "The ID of the book to move the page to",
                    "required": False
                },
                "chapter_id": {
                    "type": "int",
                    "description": "The ID of the chapter to move the page to",
                    "required": False
                },
                "name": {
                    "type": "string",
                    "description": "The new name of the page",
                    "required": False
                },
                "markdown": {
                    "type": "string",
                    "description": "The new page content in Markdown format",
                    "required": False
                },
                "html": {
                    "type": "string",
                    "description": "The new page content in HTML format",
                    "required": False
                },
                "tags": {
                    "type": "list",
                    "description": "A new list of tag objects (each with 'name' and 'value')",
                    "required": False
                },
                "priority": {
                    "type": "int",
                    "description": "New page priority",
                    "required": False
                }
            }
        }
        return json.dumps(info)

    if not isinstance(id, int) or id <= 0:
        return json.dumps({"error": "Valid page ID is required"})
    if not any([book_id, chapter_id, name, markdown, html, tags, priority]):
        return json.dumps({"error": "At least one field to update must be provided"})
    if markdown and html:
        return json.dumps({"error": "Cannot specify both markdown and html content"})

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

        # Get current page data first
        try:
            current_page = session.get(
                f"{base_url}/api/pages/{id}",
                headers=headers,
                timeout=30
            )
            current_page.raise_for_status()
            current_data = current_page.json()
        except requests.exceptions.RequestException as e:
            return json.dumps({"error": f"Failed to retrieve current page data - {str(e)}"})

        # Prepare update payload with current values as defaults
        payload = {
            "name": name if name is not None else current_data.get("name", ""),
        }
        if book_id is not None:
            payload["book_id"] = book_id
        if chapter_id is not None:
            payload["chapter_id"] = chapter_id
        if markdown is not None:
            payload["markdown"] = markdown
        if html is not None:
            payload["html"] = html
        if tags is not None:
            payload["tags"] = tags
        if priority is not None:
            payload["priority"] = priority

        response = session.put(
            f"{base_url}/api/pages/{id}",
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
    print("Testing update_page tool...")
    
    # Set up environment with credentials
    os.environ["BS_URL"] = "https://knowledge.oculair.ca"
    os.environ["BS_TOKEN_ID"] = "POnHR9Lbvm73T2IOcyRSeAqpA8bSGdMT"
    os.environ["BS_TOKEN_SECRET"] = "735wM5dScfUkcOy7qcrgqQ1eC5fBF7IE"
    
    print("\nConfiguration:")
    print(f"API Base URL: {os.environ.get('BS_URL')}")
    print(f"Authorization header: Token {os.environ.get('BS_TOKEN_ID')}:{os.environ.get('BS_TOKEN_SECRET')[:10]}...")

    # Retrieve tool info
    print("\nTool Information:")
    tool_info = update_page("__tool_info__", 0)
    print(json.dumps(json.loads(tool_info), indent=4))

    # Example page update
    print("\nUpdating test page (ID: 3)...")
    try:
        updated_page = update_page(
            3,  # Update our test page
            name="Updated Test Page",
            markdown="# Updated Test Page\n\nThis page has been updated via the API.",
            tags=[{"name": "updated", "value": "true"}]
        )
        response = json.loads(updated_page)
        if "error" in response:
            print(f"Error updating page: {response['error']}")
        else:
            print("Page updated successfully!")
            print(json.dumps(response, indent=2))
    except Exception as e:
        print(f"Error during test: {str(e)}")