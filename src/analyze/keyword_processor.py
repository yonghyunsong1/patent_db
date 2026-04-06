import json
import pandas as pd
import os
import glob
from datetime import datetime

def extract_company_name(doc):
    """
    Try to find the assignee/applicant company name by searching the most
    likely USPTO bags (assigneeBag, partyBag, and their versions inside
    applicationMetaData), while avoiding law‑firm‑like names.
    """

    def looks_like_law_firm(name: str) -> bool:
        n = name.upper()
        law_terms = [
            " LLP", " L.L.P", " L L P",
            " ATTORNEY", " ATTORNEYS",
            " ATTORNEY AT LAW", " ATTORNEYS AT LAW",
            " LAW FIRM", " LAW GROUP", " LAW OFFICE",
            " PC", " P.C.", " P C",
            " ESQ", " ESQUIRE",
            " LEGAL", " ADVOCATE", " BARRISTER", " SOLICITOR"
        ]
        return any(term in n for term in law_terms)

    def search_org_fields(node):
        """
        Recursively search for common organization/applicant/assignee fields
        within the given subtree.
        """
        candidates = []

        def walk(n):
            if isinstance(n, dict):
                for k, v in n.items():
                    kl = str(k).lower()

                    # These keys are likely to hold org / assignee / applicant names
                    if any(tag in kl for tag in [
                        "assigneeentityname",
                        "assigneeorganizationname",
                        "organizationnamestandardized",
                        "organizationname",
                        "orgname",
                        "applicantname",
                        "applicantnametext",
                        "entityname",
                        "namelineonetext",
                        "applicant",
                        "assignee"
                    ]):
                        if isinstance(v, str):
                            val = v.strip()
                        else:
                            val = str(v).strip() if not isinstance(v, (dict, list)) else ""

                        if len(val) > 2 and not looks_like_law_firm(val):
                            candidates.append(val)

                    # Recurse
                    if isinstance(v, (dict, list)):
                        walk(v)

            elif isinstance(n, list):
                for item in n:
                    walk(item)

        walk(node)
        return candidates

    # Collect candidates from the most promising bags first
    search_roots = []

    # Top‑level assignee/party bags
    if 'assigneeBag' in doc:
        search_roots.append(doc['assigneeBag'])
    if 'partyBag' in doc:
        search_roots.append(doc['partyBag'])

    # applicationMetaData.* versions
    app_meta = doc.get('applicationMetaData', {})
    if isinstance(app_meta, dict):
        if 'assigneeBag' in app_meta:
            search_roots.append(app_meta['assigneeBag'])
        if 'partyBag' in app_meta:
            search_roots.append(app_meta['partyBag'])

    candidates = []
    for root in search_roots:
        candidates.extend(search_org_fields(root))

    # If we didn’t find anything in the obvious places, do a limited fallback
    # over applicationMetaData only (not the whole doc).
    if not candidates and isinstance(app_meta, dict):
        candidates.extend(search_org_fields(app_meta))

    # Final selection logic
    if candidates:
        # remove exact duplicates
        candidates = list(dict.fromkeys(candidates))

        # Prefer non–law‑firm names (we already filtered, but keep this just in case)
        non_law = [c for c in candidates if not looks_like_law_firm(c)]
        choice_pool = non_law if non_law else candidates

        # Heuristic: pick the shortest reasonably long name
        best = sorted(choice_pool, key=len)[0]
        return best.title()

    # As an ultimate fallback, look for a generic nameLineOneText anywhere
    def search_name_line_one(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k.lower() == "namelineonetext":
                    val = str(v).strip()
                    if len(val) > 2 and not looks_like_law_firm(val):
                        return val
                if isinstance(v, (dict, list)):
                    res = search_name_line_one(v)
                    if res:
                        return res
        elif isinstance(node, list):
            for item in node:
                res = search_name_line_one(item)
                if res:
                    return res
        return None

    fallback = search_name_line_one(app_meta) or search_name_line_one(doc)
    if fallback:
        return fallback.title()

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