import json
import requests
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def delete_bookshelf(id: int) -> str:
    """
    Deletes a bookshelf from Bookstack.

    This function supports two usage scenarios:
      1) Deleting a bookshelf
      2) Retrieving the tool's metadata by passing id="__tool_info__"

    Args:
        id (int): The ID of the bookshelf to delete

    Returns:
        str: JSON-formatted string containing the response
    """
    if id == "__tool_info__":
        info = {
            "name": "delete_bookshelf",
            "description": "Deletes a bookshelf from Bookstack",
            "args": {
                "id": {
                    "type": "int",
                    "description": "The ID of the bookshelf to delete",
                    "required": True
                }
            }
        }
        return json.dumps(info)

    if not isinstance(id, int) or id <= 0:
        return json.dumps({"error": "Valid bookshelf ID is required"})

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

        response = session.delete(
            f"{base_url}/api/shelves/{id}",
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return json.dumps({"success": True, "message": f"Bookshelf with ID {id} deleted successfully"})
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Network or HTTP error - {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"Unexpected error - {str(e)}"})
    finally:
        session.close()

if __name__ == "__main__":
    print("Testing delete_bookshelf tool...")
    
    # Set up environment with credentials
    os.environ["BS_URL"] = "https://knowledge.oculair.ca"
    os.environ["BS_TOKEN_ID"] = "POnHR9Lbvm73T2IOcyRSeAqpA8bSGdMT"
    os.environ["BS_TOKEN_SECRET"] = "735wM5dScfUkcOy7qcrgqQ1eC5fBF7IE"
    
    print("\nConfiguration:")
    print(f"API Base URL: {os.environ.get('BS_URL')}")
    print(f"Authorization header: Token {os.environ.get('BS_TOKEN_ID')}:{os.environ.get('BS_TOKEN_SECRET')[:10]}...")

    # Retrieve tool info
    print("\nTool Information:")
    tool_info = delete_bookshelf("__tool_info__")
    print(json.dumps(json.loads(tool_info), indent=4))

    # Example bookshelf deletion
    print("\nDeleting test bookshelf (ID: 3)...")
    try:
        result = delete_bookshelf(3)  # Delete our test bookshelf
        response = json.loads(result)
        if "error" in response:
            print(f"Error deleting bookshelf: {response['error']}")
        else:
            print("Bookshelf deleted successfully!")
            print(json.dumps(response, indent=2))
    except Exception as e:
        print(f"Error during test: {str(e)}")