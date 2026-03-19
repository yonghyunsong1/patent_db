import requests
import json

def test_patentsview_cpc():
    # PatentsView is the USPTO's official API for data researchers
    url = "https://api.patentsview.org/patents/query"
    
    # We want to find patents where the CPC Subgroup exactly matches A61D 19/00
    # No weird escaping, no space bugs. Just the exact code.
    query = {
        "q": {"cpc_subgroup_id": "A61D19/00"},
        # We tell it exactly what fields we want back
        "f": ["patent_number", "patent_title", "patent_date", "cpc_subgroup_id"]
    }
    
    # PatentsView requires the query to be passed as a string parameter
    payload = {
        "q": json.dumps(query["q"]),
        "f": json.dumps(query["f"]),
        "o": json.dumps({"per_page": 5}) # Get 5 results
    }

    print("🚀 Querying the USPTO PatentsView Database for A61D19/00...\n")

    try:
        response = requests.get(url, params=payload)
        
        if response.status_code == 200:
            data = response.json()
            patents = data.get('patents', [])
            
            if patents:
                print(f"✅ SUCCESS! Found {data.get('count')} total patents in this CPC class.\n")
                
                for i, doc in enumerate(patents, 1):
                    print(f"📄 PATENT {i}: {doc['patent_title']}")
                    print(f"   -> Patent #: {doc['patent_number']}")
                    print(f"   -> Date:     {doc['patent_date']}")
                    
                    # Extract CPCs to verify
                    cpc_list = []
                    for cpc in doc.get('cpcs', []):
                        if cpc.get('cpc_subgroup_id'):
                            cpc_list.append(cpc['cpc_subgroup_id'])
                            
                    print(f"   -> CPCs attached: {cpc_list}\n")
            else:
                print("⚠️ 0 records returned.")
                
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_patentsview_cpc()