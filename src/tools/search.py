import json
import requests
import os
import argparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, environment variables should be set manually
    pass

def search(query: str, page: int = None, count: int = None) -> str:
    """
    Searches content (shelves, books, chapters, pages) in BookStack.

    This function supports two usage scenarios:
      1) Performing a search with the given query and optional pagination
      2) Retrieving the tool's metadata by passing query="__tool_info__"

    Args:
        query (str): The search query string. Supports advanced BookStack search syntax.
        page (int, optional): The page number for pagination.
        count (int, optional): The number of results per page (max 100).

    Returns:
        str: JSON-formatted string containing the response
    """
    if query == "__tool_info__":
        info = {
            "name": "search",
            "description": "Searches content (shelves, books, chapters, pages) in BookStack. Uses advanced search syntax.",
            "args": {
                "query": {
                    "type": "str",
                    "description": "The search query string. Supports advanced BookStack search syntax.",
                    "required": True
                },
                "page": {
                    "type": "int",
                    "description": "The page number for pagination.",
                    "required": False
                },
                "count": {
                    "type": "int",
                    "description": "The number of results per page (max 100).",
                    "required": False
                }
            }
        }
        return json.dumps(info)

    if not isinstance(query, str) or not query.strip():
        return json.dumps({"error": "Valid search query is required"})

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

        api_url = f"{base_url}/api/search"
        headers = {
            "Authorization": f"Token {token_id}:{token_secret}",
            "Content-Type": "application/json"
        }
        params = {"query": query}

        if page is not None:
            params["page"] = page
        if count is not None:
            params["count"] = count

        response = session.get(api_url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        # Parse the full response
        full_data = response.json()
        
        # Extract and simplify the results
        simplified_results = []
        for item in full_data.get('data', []):
            # Extract basic info
            title = item.get('name', 'Untitled')
            url = item.get('url', '')
            item_type = item.get('type', 'unknown')
            
            # Try to get a summary from preview_html content, fallback to description
            summary = ""
            if 'preview_html' in item and 'content' in item['preview_html']:
                # Clean up HTML tags and get first line
                import re
                content = item['preview_html']['content']
                # Remove HTML tags
                clean_content = re.sub(r'<[^>]+>', '', content)
                # Get first sentence or first 100 chars
                clean_content = clean_content.strip()
                if clean_content:
                    sentences = clean_content.split('.')
                    summary = sentences[0][:100] + ('...' if len(sentences[0]) > 100 else '')
            
            # If no summary from preview, try description
            if not summary and 'description' in item:
                summary = item['description'][:100] + ('...' if len(item['description']) > 100 else '')
            
            simplified_results.append({
                'title': title,
                'url': url,
                'type': item_type,
                'summary': summary or 'No summary available'
            })
        
        # Return simplified format with total count
        simplified_response = {
            'results': simplified_results,
            'total': full_data.get('total', len(simplified_results))
        }
        
        return json.dumps(simplified_response)
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Network or HTTP error - {str(e)}", "status_code": getattr(response, 'status_code', None) if 'response' in locals() else None})
    except Exception as e:
        return json.dumps({"error": f"Unexpected error - {str(e)}"})
    finally:
        if 'session' in locals():
            session.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search content in BookStack")
    parser.add_argument("--query", required=True, help="The search query string")
    parser.add_argument("--page", type=int, help="The page number for pagination")
    parser.add_argument("--count", type=int, help="The number of results per page (max 100)")
    parser.add_argument("--__tool_info__", help="Tool information (for consistency)")
    
    args = parser.parse_args()
    
    result = search(args.query, args.page, args.count)
    print(result)