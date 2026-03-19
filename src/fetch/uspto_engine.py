import requests
import time
import os
from dotenv import load_dotenv

class USPTO_ODP_Engine:
    """The core engine for securely querying the USPTO Open Data Portal."""
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("USPTO_API_KEY")
        
        if not self.api_key:
            raise ValueError("CRITICAL: API key not found in .env file.")

        self.url = "https://api.uspto.gov/api/v1/patent/applications/search"
        self.headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'X-API-KEY': self.api_key
        }
        
        self.SLEEP_AFTER_429 = 5.0 
        self.HTTP_RETRY = 5

    def execute_query(self, search_string, max_records=100):
        """
        Executes a paginated search query against the USPTO.
        search_string: The exact string to pass to the 'q' parameter.
        """
        all_docs = []
        offset = 0
        limit = 100 
        
        while offset < max_records:
            payload = {
                "q": search_string,
                "pagination": {
                    "offset": offset,
                    "limit": limit
                },
                "sort": [
                    {
                        "field": "applicationMetaData.filingDate",
                        "order": "desc" 
                    }
                ],
                "fields": [
                    "applicationNumberText",
                    "applicationMetaData.patentNumber",
                    "applicationMetaData.inventionTitle",
                    "applicationMetaData.applicationStatusDescriptionText",
                    "applicationMetaData.filingDate",
                    "applicantBag",
                    "assigneeBag", 
                    "correspondenceAddressBag"
                ]
            }

            docs = self._make_request(payload)
            
            if not docs:
                break 
                
            all_docs.extend(docs)
            print(f"  -> Pulled {len(docs)} records (Offset: {offset}).")
            
            if len(docs) < limit:
                break 
                
            offset += limit
            time.sleep(1) 

        return all_docs[:max_records]

    def _make_request(self, payload, retry=0):
        try:
            response = requests.post(self.url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('patentFileWrapperDataBag', [])
            elif response.status_code == 404:
                print("  -> 0 matching records found.")
                return []
            elif response.status_code == 429: 
                if retry < self.HTTP_RETRY:
                    print(f"  -> HTTP 429 Rate Limit. Sleeping {self.SLEEP_AFTER_429}s and retrying...")
                    time.sleep(self.SLEEP_AFTER_429)
                    return self._make_request(payload, retry + 1)
                else:
                    return []
            else:
                print(f"  -> HTTP {response.status_code}: {response.text}")
                return []
        except requests.exceptions.RequestException as e:
            print(f"  -> Connection Error: {e}")
            return []