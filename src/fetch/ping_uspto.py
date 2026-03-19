import requests
import json
import os
from dotenv import load_dotenv

def ping_uspto():
    load_dotenv()
    api_key = os.getenv("USPTO_API_KEY")
    
    if not api_key:
        print("❌ ERROR: API key not found in .env file.")
        return

    # The official POST search endpoint
    url = "https://api.uspto.gov/api/v1/patent/applications/search"
    
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'X-API-KEY': api_key
    }

    # The exact "Advanced Syntax" JSON payload from the PDF
    # We are searching for the word "Apple", limiting to 1 result, 
    # and asking specifically for the Law Firm and Applicant data fields.
    payload = {
        "q": "Apple",
        "pagination": {
            "offset": 0,
            "limit": 1
        },
        "fields": [
            "applicationNumberText",
            "applicationMetaData.inventionTitle",
            "applicantBag",
            "correspondenceAddressBag"
        ]
    }

    print("Pinging USPTO Open Data Portal (via POST JSON request)...\n")
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS! The POST JSON syntax works perfectly.")
            
            data = response.json()
            docs = data.get('patentFileWrapperDataBag', [])
            
            if docs:
                print("\n--- Sample Data Extracted ---")
                doc = docs[0]
                print(f"Application Number: {doc.get('applicationNumberText')}")
                
                # Digging into the nested data based on their Field Dictionary
                meta = doc.get('applicationMetaData', {})
                print(f"Title: {meta.get('inventionTitle')}")
                
                # Check for Law Firm (Correspondence Address)
                address_bag = doc.get('correspondenceAddressBag', [])
                if address_bag:
                    print(f"Law Firm / Address: {address_bag[0].get('nameLineOneText')}")
                else:
                    print("Law Firm: None listed")
            else:
                print("No documents returned.")
                
        else:
            print("❌ SYNTAX ERROR.")
            print(f"Server says: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ CONNECTION ERROR: {e}")

if __name__ == "__main__":
    ping_uspto()