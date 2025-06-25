import json
import requests
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_page(name: str, book_id: int = None, chapter_id: int = None, markdown: str = None, html: str = None, tags: list = None, priority: int = None) -> str:
    """
    Creates a new page in Bookstack.

    This function supports two usage scenarios:
      1) Creating a page
      2) Retrieving the tool's metadata by passing name="__tool_info__"

    Args:
        name (str): The name of the page
        book_id (int, optional): The ID of the book to create the page in
        chapter_id (int, optional): The ID of the chapter to create the page in
        markdown (str, optional): The page content in Markdown format
        html (str, optional): The page content in HTML format
        tags (list, optional): A list of tag objects (each with 'name' and 'value')
        priority (int, optional): Page priority

    Returns:
        str: JSON-formatted string containing the response
    """
    if name == "__tool_info__":
        info = {
            "name": "create_page",
            "description": "Creates a new page in Bookstack",
            "args": {
                "name": {
                    "type": "string",
                    "description": "The name of the page",
                    "required": True
                },
                "book_id": {
                    "type": "int",
                    "description": "The ID of the book to create the page in",
                    "required": False
                },
                "chapter_id": {
                    "type": "int",
                    "description": "The ID of the chapter to create the page in",
                    "required": False
                },
                "markdown": {
                    "type": "string",
                    "description": "The page content in Markdown format",
                    "required": False
                },
                "html": {
                    "type": "string",
                    "description": "The page content in HTML format",
                    "required": False
                },
                "tags": {
                    "type": "list",
                    "description": "A list of tag objects (each with 'name' and 'value')",
                    "required": False
                },
                "priority": {
                    "type": "int",
                    "description": "Page priority",
                    "required": False
                }
            }
        }
        return json.dumps(info)

    if not name:
        return json.dumps({"error": "Page name is required"})
    if not book_id and not chapter_id:
        return json.dumps({"error": "Either book_id or chapter_id is required"})
    if book_id and chapter_id:
        return json.dumps({"error": "Cannot specify both book_id and chapter_id"})
    if not markdown and not html:
        return json.dumps({"error": "Either markdown or html content is required"})
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

        payload = {
            "name": name
        }
        if book_id:
            payload["book_id"] = book_id
        if chapter_id:
            payload["chapter_id"] = chapter_id
        if markdown:
            payload["markdown"] = markdown
        if html:
            payload["html"] = html
        if tags:
            payload["tags"] = tags
        if priority is not None:
            payload["priority"] = priority

        response = session.post(
            f"{base_url}/api/pages",
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
    print("Testing create_page tool...")
    
    # Set up environment with credentials
    os.environ["BS_URL"] = "https://knowledge.oculair.ca"
    os.environ["BS_TOKEN_ID"] = "POnHR9Lbvm73T2IOcyRSeAqpA8bSGdMT"
    os.environ["BS_TOKEN_SECRET"] = "735wM5dScfUkcOy7qcrgqQ1eC5fBF7IE"
    
    print("\nConfiguration:")
    print(f"API Base URL: {os.environ.get('BS_URL')}")
    print(f"Authorization header: Token {os.environ.get('BS_TOKEN_ID')}:{os.environ.get('BS_TOKEN_SECRET')[:10]}...")

    # Retrieve tool info
    print("\nTool Information:")
    tool_info = create_page("__tool_info__", "")
    print(json.dumps(json.loads(tool_info), indent=4))

    # Example page creation
    print("\nCreating test page...")
    try:
        new_page = create_page(
            name="Test Page",
            book_id=7,  # Using the book ID from create_book.py test
            markdown="# Test Page\n\nThis is a test page created via the API.",
            tags=[{"name": "test", "value": "api"}]
        )
        response = json.loads(new_page)
        if "error" in response:
            print(f"Error creating page: {response['error']}")
        else:
            print("Page created successfully!")
            print(json.dumps(response, indent=2))
    except Exception as e:
        print(f"Error during test: {str(e)}")