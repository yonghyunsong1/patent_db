import json
import pandas as pd
import os
import glob
from datetime import datetime

def extract_company_name(doc):
    """
    Hunts through the USPTO JSON schema to find the Company/Assignee.
    Ignores empty strings and handles different API schemas.
    """
    # 1. Check flat fields first
    for flat_key in ['assigneeEntityName', 'assigneeOrganizationName']:
        val = doc.get(flat_key)
        if val and len(str(val).strip()) > 2: 
            return str(val).strip().title()
            
    # 2. Recursive search function that IGNORES empty strings
    def search_dict_for_org(d):
        if isinstance(d, dict):
            for key in ['organizationNameStandardized', 'organizationName']:
                val = d.get(key)
                if val and len(str(val).strip()) > 2:
                    return str(val).strip()
            for v in d.values():
                res = search_dict_for_org(v)
                if res: return res
        elif isinstance(d, list):
            for item in d:
                res = search_dict_for_org(item)
                if res: return res
        return None
        
    # Search the two most common JSON bags
    found = search_dict_for_org(doc.get('partyBag', {}))
    if found: return found.title()
    
    found = search_dict_for_org(doc.get('assigneeBag', {}))
    if found: return found.title()

    # 3. Fallback: The standard Applicant Name line
    party_bag = doc.get('partyBag', {})
    applicants = party_bag.get('applicantBagOrAssigneeBag', [])
    if applicants and isinstance(applicants, list) and len(applicants) > 0:
        val = applicants[0].get('nameLineOneText')
        if val and len(str(val).strip()) > 2:
            return str(val).strip().title()
            
    return "Unknown"

def load_and_flatten_data(json_path):
    print(f"Loading raw data from: {os.path.basename(json_path)}")
    if not os.path.exists(json_path):
        return None

    with open(json_path, 'r') as f:
        raw_data = json.load(f)

    clean_records = []
    for doc in raw_data:
        keyword = doc.get('Search_Keyword', 'Unknown')
        technology = doc.get('Search_Target_Technology', 'Unknown')
        app_number = doc.get('applicationNumberText', 'Unknown')
        
        meta = doc.get('applicationMetaData', {})
        patent_number = meta.get('patentNumber', 'None (Not Granted)')
        status = meta.get('applicationStatusDescriptionText', 'Unknown')
        title = meta.get('inventionTitle', 'Unknown')
        filing_date = meta.get('filingDate', 'Unknown')
        
        # Extract Law Firm
        address_bag = doc.get('correspondenceAddressBag', [])
        law_firm = "Unknown / Pro Se"
        address_line_2 = ""
        if address_bag and len(address_bag) > 0:
            law_firm = str(address_bag[0].get('nameLineOneText', 'Unknown')).title()
            address_line_2 = str(address_bag[0].get('nameLineTwoText', ''))

        # Extract Company using the new brute-force function
        company = extract_company_name(doc)

        clean_records.append({
            "Keyword": keyword,
            "Technology_Category": technology,
            "Company": company,
            "App_Number": app_number,
            "Filing_Date": filing_date,
            "Raw_Status": status,
            "Law_Firm": law_firm,
            "Attorney_Notes": address_line_2,
            "Title": title
        })

    df = pd.DataFrame(clean_records)
    if not df.empty:
        df['Filing_Date'] = pd.to_datetime(df['Filing_Date'], errors='coerce')
        df = df.sort_values(by=['Filing_Date'], ascending=[False])
        
    return df

def categorize_status(status_string):
    status = str(status_string).upper()
    if 'PROVISIONAL' in status: return 'Provisional (Placeholder)'
    elif 'PCT' in status or 'INTERNATIONAL' in status: return 'PCT (Intl. Placeholder)'
    elif 'PATENTED' in status or 'ISSUED' in status or 'ALLOW' in status: return 'Enforceable (Granted)'
    elif 'ABANDON' in status: return 'Abandoned (Wastage)'
    else: return 'Pipeline (Active/Pending)'
    
def generate_landscape_reports(df, root_dir):
    csv_dir = os.path.join(root_dir, "data", "processed")
    os.makedirs(csv_dir, exist_ok=True)

    df['Lifecycle_Category'] = df['Raw_Status'].apply(categorize_status)
    
    keyword = df['Keyword'].iloc[0]
    safe_name = keyword.replace(" ", "_").replace("-", "_").lower()
    
    csv_path = os.path.join(csv_dir, f"tech_{safe_name}_landscape.csv")
    df.to_csv(csv_path, index=False)
    print(f"✅ Processed data saved for: {keyword}")

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    root_dir = os.path.dirname(os.path.dirname(current_dir)) 
    raw_dir = os.path.join(root_dir, "data", "raw")
    
    json_files = glob.glob(os.path.join(raw_dir, "kw_*_raw.json"))
    
    if not json_files:
        print(f"❌ No keyword JSON files found. Run your fetcher first.")
        return

    print("Extracting structured data from raw JSON...\n")
    for json_path in json_files:
        df = load_and_flatten_data(json_path)
        if df is not None and not df.empty:
            generate_landscape_reports(df, root_dir) 
            
    print("\n✅ Processing complete! You can now run the plotter.")

if __name__ == "__main__":
    main()