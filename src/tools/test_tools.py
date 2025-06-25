import os
import json
import time
from create_book import create_book
from create_chapter import create_chapter
from create_page import create_page
from create_bookshelf import create_bookshelf
from read_book import read_book
from read_chapter import read_chapter
from read_page import read_page
from read_bookshelf import read_bookshelf
from list_books import list_books
from list_chapters import list_chapters
from list_pages import list_pages
from list_bookshelves import list_bookshelves
from update_book import update_book
from update_chapter import update_chapter
from update_page import update_page
from update_bookshelf import update_bookshelf
from delete_book import delete_book
from delete_chapter import delete_chapter
from delete_page import delete_page
from delete_bookshelf import delete_bookshelf

def setup_environment():
    """Set up the environment variables for testing."""
    os.environ["BS_URL"] = "https://knowledge.oculair.ca"
    os.environ["BS_TOKEN_ID"] = "POnHR9Lbvm73T2IOcyRSeAqpA8bSGdMT"
    os.environ["BS_TOKEN_SECRET"] = "735wM5dScfUkcOy7qcrgqQ1eC5fBF7IE"

def parse_response(response_str):
    """Parse JSON response and handle errors."""
    try:
        response = json.loads(response_str)
        if "error" in response:
            return None, response["error"]
        return response, None
    except json.JSONDecodeError as e:
        return None, f"Failed to parse response: {str(e)}"

def run_test(test_name, func, *args, **kwargs):
    """Run a test and print the result."""
    print(f"\n{'='*20} Testing {test_name} {'='*20}")
    try:
        result = func(*args, **kwargs)
        response, error = parse_response(result)
        if error:
            print(f"❌ Test failed: {error}")
            return None
        print("✅ Test passed")
        print(f"Response: {json.dumps(response, indent=2)}")
        return response
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        return None

def main():
    print("\n🚀 Starting Bookstack Tools Test Suite")
    print("Setting up environment variables...")
    setup_environment()

    # Print configuration for verification
    print(f"\nAPI Base URL: {os.environ.get('BS_URL')}")
    print(f"Authorization header: Token {os.environ.get('BS_TOKEN_ID')}:{os.environ.get('BS_TOKEN_SECRET')[:10]}...")
    
    created_ids = {}
    
    # Test Create Operations
    print("\n📝 Testing Create Operations")
    
    # Create a book
    book_response = run_test("create_book", create_book, 
        "Test Suite Book", "This is a test book created by the test suite.")
    if book_response:
        created_ids["book"] = book_response.get("id")
        print(f"Created book with ID: {created_ids['book']}")
    
    if "book" in created_ids:
        # Create a chapter
        chapter_response = run_test("create_chapter", create_chapter,
            created_ids["book"], "Test Chapter", "This is a test chapter.")
        if chapter_response:
            created_ids["chapter"] = chapter_response.get("id")
            print(f"Created chapter with ID: {created_ids['chapter']}")
        
        # Create a page in the chapter
        if "chapter" in created_ids:
            page_response = run_test("create_page", create_page,
                "Test Page", chapter_id=created_ids["chapter"],
                markdown="# Test Page\nThis is a test page created by the test suite.")
            if page_response:
                created_ids["page"] = page_response.get("id")
                print(f"Created page with ID: {created_ids['page']}")
    
    # Create a bookshelf
    if "book" in created_ids:
        bookshelf_response = run_test("create_bookshelf", create_bookshelf,
            "Test Suite Shelf", "This is a test bookshelf.",
            books=[created_ids["book"]])
        if bookshelf_response:
            created_ids["bookshelf"] = bookshelf_response.get("id")
            print(f"Created bookshelf with ID: {created_ids['bookshelf']}")

    # Allow time for changes to propagate
    time.sleep(2)

    # Test Read Operations
    print("\n📖 Testing Read Operations")
    if "book" in created_ids:
        run_test("read_book", read_book, created_ids["book"])
    if "chapter" in created_ids:
        run_test("read_chapter", read_chapter, created_ids["chapter"])
    if "page" in created_ids:
        run_test("read_page", read_page, created_ids["page"])
    if "bookshelf" in created_ids:
        run_test("read_bookshelf", read_bookshelf, created_ids["bookshelf"])

    # Test List Operations
    print("\n📋 Testing List Operations")
    run_test("list_books", list_books)
    run_test("list_chapters", list_chapters)
    run_test("list_pages", list_pages)
    run_test("list_bookshelves", list_bookshelves)

    # Test Update Operations
    print("\n✏️ Testing Update Operations")
    if "book" in created_ids:
        run_test("update_book", update_book, created_ids["book"],
            name="Updated Test Book",
            description="This book has been updated by the test suite.")
    if "chapter" in created_ids:
        run_test("update_chapter", update_chapter, created_ids["chapter"],
            name="Updated Test Chapter",
            description="This chapter has been updated by the test suite.")
    if "page" in created_ids:
        run_test("update_page", update_page, created_ids["page"],
            name="Updated Test Page",
            markdown="# Updated Test Page\nThis page has been updated by the test suite.")
    if "bookshelf" in created_ids:
        run_test("update_bookshelf", update_bookshelf, created_ids["bookshelf"],
            name="Updated Test Shelf",
            description="This bookshelf has been updated by the test suite.")

    # Allow time for changes to propagate
    time.sleep(2)

    # Test Delete Operations
    print("\n🗑️ Testing Delete Operations")
    # Delete in reverse order to handle dependencies
    if "page" in created_ids:
        run_test("delete_page", delete_page, created_ids["page"])
    if "chapter" in created_ids:
        run_test("delete_chapter", delete_chapter, created_ids["chapter"])
    if "book" in created_ids:
        run_test("delete_book", delete_book, created_ids["book"])
    if "bookshelf" in created_ids:
        run_test("delete_bookshelf", delete_bookshelf, created_ids["bookshelf"])

    print("\n🏁 Test Suite Completed")

if __name__ == "__main__":
    main()