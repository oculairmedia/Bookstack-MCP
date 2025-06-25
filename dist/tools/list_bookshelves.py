import json
import requests
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def list_bookshelves(offset: int = 0, count: int = 100) -> str:
    """
    Lists all bookshelves in Bookstack with pagination support.

    This function supports two usage scenarios:
      1) Listing all bookshelves
      2) Retrieving the tool's metadata by passing offset="__tool_info__"

    Args:
        offset (int, optional): Number of records to skip. Defaults to 0.
        count (int, optional): Number of records to take. Defaults to 100.

    Returns:
        str: JSON-formatted string containing the response
    """
    if offset == "__tool_info__":
        info = {
            "name": "list_bookshelves",
            "description": "Lists all bookshelves in Bookstack with pagination support",
            "args": {
                "offset": {
                    "type": "int",
                    "description": "Number of records to skip",
                    "required": False
                },
                "count": {
                    "type": "int",
                    "description": "Number of records to take",
                    "required": False
                }
            }
        }
        return json.dumps(info)

    if not isinstance(offset, int) or offset < 0:
        return json.dumps({"error": "Invalid offset value"})
    if not isinstance(count, int) or count <= 0:
        return json.dumps({"error": "Invalid count value"})

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

        params = {
            "offset": offset,
            "count": count
        }

        response = session.get(
            f"{base_url}/api/shelves",
            headers=headers,
            params=params,
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
    print("Testing list_bookshelves tool...")
    
    # Set up environment with credentials
    os.environ["BS_URL"] = "https://knowledge.oculair.ca"
    os.environ["BS_TOKEN_ID"] = "POnHR9Lbvm73T2IOcyRSeAqpA8bSGdMT"
    os.environ["BS_TOKEN_SECRET"] = "735wM5dScfUkcOy7qcrgqQ1eC5fBF7IE"
    
    print("\nConfiguration:")
    print(f"API Base URL: {os.environ.get('BS_URL')}")
    print(f"Authorization header: Token {os.environ.get('BS_TOKEN_ID')}:{os.environ.get('BS_TOKEN_SECRET')[:10]}...")

    # Retrieve tool info
    print("\nTool Information:")
    tool_info = list_bookshelves("__tool_info__")
    print(json.dumps(json.loads(tool_info), indent=4))

    # Example list retrieval
    print("\nRetrieving list of bookshelves...")
    try:
        bookshelves_list = list_bookshelves()
        response = json.loads(bookshelves_list)
        if "error" in response:
            print(f"Error retrieving bookshelves: {response['error']}")
        else:
            print("Bookshelves retrieved successfully!")
            print(json.dumps(response, indent=2))
    except Exception as e:
        print(f"Error during test: {str(e)}")