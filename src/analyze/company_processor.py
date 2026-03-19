import json
import pandas as pd
import os
import glob
from datetime import datetime

def load_and_flatten_data(json_path):
    print(f"Loading raw data from: {os.path.basename(json_path)}")
    if not os.path.exists(json_path):
        print("❌ Error: Could not find the JSON file.")
        return None

    with open(json_path, 'r') as f:
        raw_data = json.load(f)

    clean_records = []
    for doc in raw_data:
        target_company = doc.get('Search_Target_Company', 'Unknown')
        app_number = doc.get('applicationNumberText', 'Unknown')
        
        meta = doc.get('applicationMetaData', {})
        patent_number = meta.get('patentNumber', 'None (Not Granted)')
        status = meta.get('applicationStatusDescriptionText', 'Unknown')
        title = meta.get('inventionTitle', 'Unknown')
        filing_date = meta.get('filingDate', 'Unknown')
        
        address_bag = doc.get('correspondenceAddressBag', [])
        law_firm = "Unknown / Pro Se"
        address_line_2 = ""
        
        if address_bag and len(address_bag) > 0:
            law_firm = address_bag[0].get('nameLineOneText', 'Unknown')
            address_line_2 = address_bag[0].get('nameLineTwoText', '')

        clean_records.append({
            "Target_Company": target_company,
            "App_Number": app_number,
            "Patent_Number": patent_number,
            "Filing_Date": filing_date,
            "Raw_Status": status,
            "Law_Firm": law_firm,
            "Attorney_Notes": address_line_2,
            "Title": title
        })

    df = pd.DataFrame(clean_records)
    
    if not df.empty:
        df['Filing_Date'] = pd.to_datetime(df['Filing_Date'], errors='coerce')
        df = df.sort_values(by=['Target_Company', 'Filing_Date'], ascending=[True, False])
        
    return df

def categorize_status(status_string):
    """Buckets messy USPTO statuses into standard IP Due Diligence categories."""
    status = str(status_string).upper()
    
    # Check for placeholders FIRST so they don't get accidentally lumped into 'Pending' or 'Abandoned'
    if 'PROVISIONAL' in status:
        return 'Provisional (Placeholder)'
    elif 'PCT' in status or 'INTERNATIONAL' in status:
        return 'PCT (Intl. Placeholder)'
        
    # Then check for real application outcomes
    elif 'PATENTED' in status or 'ISSUED' in status or 'ALLOW' in status:
        return 'Enforceable (Granted)'
    elif 'ABANDON' in status:
        return 'Abandoned (Wastage)'
    else:
        return 'Pipeline (Active/Pending)'
    
def generate_diligence_reports(df, root_dir):
    """Generates a BigLaw-style IP Due Diligence Memo for each company."""
    
    csv_dir = os.path.join(root_dir, "data", "processed")
    report_dir = os.path.join(root_dir, "outputs", "reports")
    
    os.makedirs(csv_dir, exist_ok=True)
    os.makedirs(report_dir, exist_ok=True)

    # Apply the business categorization
    df['Business_Category'] = df['Raw_Status'].apply(categorize_status)
    companies = df['Target_Company'].unique()
    
    for company in companies:
        comp_df = df[df['Target_Company'] == company].copy()
        
        # Save individual CSV safely
        safe_name = company.replace(" ", "_").replace(",", "").lower()
        csv_path = os.path.join(csv_dir, f"{safe_name}_diligence_data.csv")
        comp_df.to_csv(csv_path, index=False)
        
        # Analytics calculations
        total_apps = len(comp_df)
        enforceable = len(comp_df[comp_df['Business_Category'] == 'Enforceable (Granted)'])
        abandoned = len(comp_df[comp_df['Business_Category'] == 'Abandoned (Wastage)'])
        pending = len(comp_df[comp_df['Business_Category'] == 'Pipeline (Active/Pending)'])
        
        # Allowance Rate (Granted / (Granted + Abandoned))
        resolved_cases = enforceable + abandoned
        allowance_rate = (enforceable / resolved_cases * 100) if resolved_cases > 0 else 0.0

        # Filing Velocity (Recent Activity in last 24 months)
        two_years_ago = pd.Timestamp.now() - pd.DateOffset(years=2)
        recent_filings = len(comp_df[comp_df['Filing_Date'] >= two_years_ago])

        # Generate the Memo safely
        report_path = os.path.join(report_dir, f"{safe_name}_due_diligence_memo.txt")
        
        with open(report_path, 'w') as f:
            f.write("CONFIDENTIAL IP DUE DILIGENCE SUMMARY\n")
            f.write("=" * 60 + "\n")
            f.write(f"SUBJECT ENTITY : {company.upper()}\n")
            f.write(f"REPORT DATE    : {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write(f"SCOPE          : US Filings Only (Max Sample: 200 records)\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("1. PORTFOLIO HEALTH & METRICS\n")
            f.write("-" * 60 + "\n")
            f.write(f"Total US Applications Tracked : {total_apps}\n")
            f.write(f"Enforceable Assets (Granted)  : {enforceable}  ({(enforceable/total_apps*100) if total_apps > 0 else 0:.1f}%)\n")
            f.write(f"Pipeline Assets (Pending)     : {pending}  ({(pending/total_apps*100) if total_apps > 0 else 0:.1f}%)\n")
            f.write(f"Abandoned Assets (Wastage)    : {abandoned}  ({(abandoned/total_apps*100) if total_apps > 0 else 0:.1f}%)\n\n")
            
            f.write(f">> Estimated Allowance Rate : {allowance_rate:.1f}%\n")
            f.write(f">> R&D Velocity (Filings in last 24 mos): {recent_filings} applications\n\n")

            f.write("2. OUTSIDE COUNSEL OF RECORD\n")
            f.write("-" * 60 + "\n")
            firm_counts = comp_df['Law_Firm'].value_counts()
            for firm, count in firm_counts.items():
                percentage = (count/total_apps)*100
                f.write(f"  [{count:02d} cases | {percentage:04.1f}%] {firm}\n")
                
                # Show specific attorneys handling the bulk of the work
                notes = comp_df[(comp_df['Law_Firm'] == firm) & (comp_df['Attorney_Notes'] != "")]['Attorney_Notes'].dropna().unique()
                if len(notes) > 0:
                    f.write(f"       Primary Contacts: {', '.join(notes[:2])}\n")
            
            f.write("\n3. DETAILED STATUS BREAKDOWN (USPTO RAW)\n")
            f.write("-" * 60 + "\n")
            status_counts = comp_df['Raw_Status'].value_counts()
            for status, count in status_counts.items():
                f.write(f"  - {status}: {count}\n")
                
        print(f"📄 Generated IP Memo: {os.path.basename(report_path)}")

def main():
    # Bulletproof Pathing
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    root_dir = os.path.dirname(os.path.dirname(current_dir)) 
    
    raw_dir = os.path.join(root_dir, "data", "raw")
    
    # Use glob to find ALL files that match the new company fetcher naming convention
    # This prevents it from accidentally trying to process the CPC Landscape data!
    json_files = glob.glob(os.path.join(raw_dir, "company_*_raw.json"))
    
    if not json_files:
        print(f"❌ No company JSON files found in {raw_dir}. Run run_company_search.py first.")
        return

    print("Processing company portfolios...")
    
    # Loop through each file individually
    for json_path in json_files:
        df = load_and_flatten_data(json_path)
        
        if df is not None and not df.empty:
            generate_diligence_reports(df, root_dir) 
        else:
            print(f"⚠️ DataFrame is empty for {os.path.basename(json_path)}. Skipping.")

    print("\n✅ All Due Diligence memos saved to 'outputs/reports/' folder!")

if __name__ == "__main__":
    main()