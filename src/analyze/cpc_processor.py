import json
import pandas as pd
import os
import glob
from datetime import datetime

def categorize_status(status_string):
    status = str(status_string).upper()
    if 'PROVISIONAL' in status: return 'Provisional (Placeholder)'
    elif 'PCT' in status or 'INTERNATIONAL' in status: return 'PCT (Intl. Placeholder)'
    elif 'PATENTED' in status or 'ISSUED' in status or 'ALLOW' in status: return 'Enforceable (Granted)'
    elif 'ABANDON' in status: return 'Abandoned (Wastage)'
    else: return 'Pipeline (Active/Pending)'

def process_cpc_file(json_path, root_dir):
    print(f"Processing landscape data: {os.path.basename(json_path)}")
    
    with open(json_path, 'r') as f:
        raw_data = json.load(f)

    clean_records = []
    for doc in raw_data:
        tech_desc = doc.get('Search_Target_Technology', 'Unknown')
        cpc_code = doc.get('CPC_Code', 'Unknown')
        
        meta = doc.get('applicationMetaData', {})
        status = meta.get('applicationStatusDescriptionText', 'Unknown')
        
        # Get Law Firm
        address_bag = doc.get('correspondenceAddressBag', [])
        law_firm = "Unknown / Pro Se"
        if address_bag and len(address_bag) > 0:
            law_firm = address_bag[0].get('nameLineOneText', 'Unknown').upper()

        # Get Company (Assignee or Applicant)
        assignee_bag = doc.get('assigneeBag', [])
        applicant_bag = doc.get('applicantBag', [])
        company = "Unassigned"
        
        if assignee_bag and len(assignee_bag) > 0:
            company = assignee_bag[0].get('assigneeNameText', 'Unassigned').upper()
        elif applicant_bag and len(applicant_bag) > 0:
            company = applicant_bag[0].get('applicantNameText', 'Unassigned').upper()

        clean_records.append({
            "Technology": tech_desc,
            "CPC_Code": cpc_code,
            "Company": company,
            "Law_Firm": law_firm,
            "Filing_Date": meta.get('filingDate', 'Unknown'),
            "Raw_Status": status,
            "Business_Category": categorize_status(status)
        })

    df = pd.DataFrame(clean_records)
    df['Filing_Date'] = pd.to_datetime(df['Filing_Date'], errors='coerce')
    
    # Save CSV
    safe_name = os.path.basename(json_path).replace("_raw.json", "")
    csv_path = os.path.join(root_dir, "data", "processed", f"{safe_name}_landscape.csv")
    df.to_csv(csv_path, index=False)

    # Generate Landscape Text Report
    report_path = os.path.join(root_dir, "outputs", "reports", f"{safe_name}_landscape_report.txt")
    with open(report_path, 'w') as f:
        f.write(f"INDUSTRY LANDSCAPE REPORT: {df['Technology'].iloc[0].upper()} ({cpc_code})\n")
        f.write("=" * 70 + "\n")
        
        f.write("\n1. TOP 10 COMPANIES DOMINATING THIS SPACE\n")
        f.write("-" * 70 + "\n")
        top_companies = df[df['Company'] != 'UNASSIGNED']['Company'].value_counts().head(10)
        for comp, count in top_companies.items():
            f.write(f"  [{count:03d} Patents] {comp}\n")
            
        f.write("\n2. TOP 10 LAW FIRMS IN THIS SPACE (Your Targets!)\n")
        f.write("-" * 70 + "\n")
        top_firms = df['Law_Firm'].value_counts().head(10)
        for firm, count in top_firms.items():
            f.write(f"  [{count:03d} Patents] {firm}\n")

    print(f"  ✅ Saved {csv_path} and Report!")

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    root_dir = os.path.dirname(os.path.dirname(current_dir)) 
    
    raw_dir = os.path.join(root_dir, "data", "raw")
    cpc_files = glob.glob(os.path.join(raw_dir, "cpc_*_raw.json"))
    
    os.makedirs(os.path.join(root_dir, "data", "processed"), exist_ok=True)
    os.makedirs(os.path.join(root_dir, "outputs", "reports"), exist_ok=True)

    for file in cpc_files:
        process_cpc_file(file, root_dir)

if __name__ == "__main__":
    main()