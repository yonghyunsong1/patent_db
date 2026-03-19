import requests
import json
import time

def search_uspto_by_cpc(cpc_code, year=None, dataset="grants", rows=5):
    if dataset == "grants":
        url = "https://developer.uspto.gov/ibd-api/v1/patent/grants"
    else:
        url = "https://developer.uspto.gov/ibd-api/v1/application/publications"

    # Construct the query
    # If a year is provided, we limit the search to prevent the USPTO database from timing out (503 error)
    if year:
        query = f'cpc:"{cpc_code}" AND publicationDate:[{year}-01-01 TO {year}-12-31]'
    else:
        query = f'cpc:"{cpc_code}"'

    params = {
        "searchText": query,
        "start": 0,
        "rows": rows
    }

    # CRITICAL: USPTO blocks default python-requests. We must mimic a real browser.
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print(f"Querying USPTO Open Data API...\nURL: {url}\nQuery: {query}\n")
    
    # Adding a basic retry mechanism since gov servers can be flaky
    max_retries = 3
    for attempt in range(max_retries):
        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            print(f"Success! Found {data.get('recordTotalQuantity', 'unknown')} total records.")
            print(f"Showing top {len(results)} results:\n")
            
            for item in results:
                patent_id = item.get("patentDocumentNumber", "N/A")
                title = item.get("inventionTitle", "N/A")
                date = item.get("publicationDate", "N/A")
                
                print(f"Patent ID: {patent_id}")
                print(f"Title:     {title}")
                print(f"Date:      {date}")
                print("-" * 40)
                
            return data
            
        elif response.status_code == 503:
            print(f"Attempt {attempt + 1} failed with 503 (Server Overloaded). Retrying in 2 seconds...")
            time.sleep(2)
        else:
            print(f"Error {response.status_code}: {response.text}")
            break
            
    print("Failed to retrieve data after multiple attempts.")
    return None

if __name__ == "__main__":
    # Test with a specific year to prevent backend database timeouts
    search_uspto_by_cpc("G06F", year=2023, dataset="grants", rows=3)