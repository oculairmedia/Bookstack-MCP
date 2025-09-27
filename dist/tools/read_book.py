import json
import requests
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def read_book(id: int) -> str:
    """
    Retrieves details of a specific book in Bookstack.

    This function supports two usage scenarios:
      1) Retrieving a book's details
      2) Retrieving the tool's metadata by passing id="__tool_info__"

    Args:
        id (int): The ID of the book to retrieve

    Returns:
        str: JSON-formatted string containing the response
    """
    if id == "__tool_info__":
        info = {
            "name": "read_book",
            "description": "Retrieves details of a specific book in Bookstack",
            "args": {
                "id": {
                    "type": "int",
                    "description": "The ID of the book to retrieve",
                    "required": True
                }
            }
        }
        return json.dumps(info)

    if not isinstance(id, int) or id <= 0:
        return json.dumps({"error": "Valid book ID is required"})

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

        response = session.get(
            f"{base_url}/api/books/{id}",
            headers=headers,
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
    print("Testing read_book tool...")
    
    # Set up environment with credentials
    os.environ["BS_URL"] = "https://knowledge.oculair.ca"
    os.environ["BS_TOKEN_ID"] = "POnHR9Lbvm73T2IOcyRSeAqpA8bSGdMT"
    os.environ["BS_TOKEN_SECRET"] = "735wM5dScfUkcOy7qcrgqQ1eC5fBF7IE"
    
    print("\nConfiguration:")
    print(f"API Base URL: {os.environ.get('BS_URL')}")
    print(f"Authorization header: Token {os.environ.get('BS_TOKEN_ID')}:{os.environ.get('BS_TOKEN_SECRET')[:10]}...")

    # Retrieve tool info
    print("\nTool Information:")
    tool_info = read_book("__tool_info__")
    print(json.dumps(json.loads(tool_info), indent=4))

    # Example book retrieval
    print("\nRetrieving test book (ID: 7)...")
    try:
        book_details = read_book(7)  # Using our test book's ID
        response = json.loads(book_details)
        if "error" in response:
            print(f"Error retrieving book: {response['error']}")
        else:
            print("Book retrieved successfully!")
            print(json.dumps(response, indent=2))
    except Exception as e:
        print(f"Error during test: {str(e)}")