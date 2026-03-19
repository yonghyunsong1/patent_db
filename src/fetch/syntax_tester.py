import requests
import json
import os
from dotenv import load_dotenv

def test_cpc_syntax():
    load_dotenv()
    api_key = os.getenv("USPTO_API_KEY")
    
    if not api_key:
        print("❌ ERROR: API key not found in .env file.")
        return

    url = "https://api.uspto.gov/api/v1/patent/applications/search"
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'X-API-KEY': api_key
    }

    # The 4 variations we are testing to see how the USPTO parses the text
    test_queries = {
        "Test 1 (Raw String)": "A61D 19/00",
        "Test 2 (Escaped Slash)": "A61D 19\\/00",
        "Test 3 (No Space)": "A61D19/00",
        "Test 4 (Specific Field Wildcard)": "cpcClassificationBag.*:A61D*"
    }

    print("🚀 Running USPTO Syntax Sandbox...\n")

    for test_name, query_string in test_queries.items():
        print(f"Trying {test_name}: {query_string}")
        
        payload = {
            "q": query_string,
            "pagination": {"offset": 0, "limit": 1}
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                docs = response.json().get('patentFileWrapperDataBag', [])
                if docs:
                    print(f"  ✅ SUCCESS! Found {len(docs)} record(s). This syntax works!\n")
                else:
                    print("  ⚠️ 200 OK, but 0 records returned.\n")
            elif response.status_code == 404:
                print("  ❌ 404: Zero records found (API rejected the format).\n")
            else:
                print(f"  ❌ Failed with status: {response.status_code}\n")
                
        except Exception as e:
            print(f"  ❌ Error: {e}\n")

if __name__ == "__main__":
    test_cpc_syntax()