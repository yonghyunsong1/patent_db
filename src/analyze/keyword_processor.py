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
        # Adjusted to grab the new fields created by your keyword fetcher
        keyword = doc.get('Search_Keyword', 'Unknown')
        technology = doc.get('Search_Target_Technology', 'Unknown')
        
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
            "Keyword": keyword,
            "Technology_Category": technology,
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
        # Sort by newest filings first
        df = df.sort_values(by=['Filing_Date'], ascending=[False])
        
    return df

def categorize_status(status_string):
    """Buckets messy USPTO statuses into standard lifecycle categories."""
    status = str(status_string).upper()
    
    if 'PROVISIONAL' in status:
        return 'Provisional (Placeholder)'
    elif 'PCT' in status or 'INTERNATIONAL' in status:
        return 'PCT (Intl. Placeholder)'
    elif 'PATENTED' in status or 'ISSUED' in status or 'ALLOW' in status:
        return 'Enforceable (Granted)'
    elif 'ABANDON' in status:
        return 'Abandoned (Wastage)'
    else:
        return 'Pipeline (Active/Pending)'
    
def generate_landscape_reports(df, root_dir):
    """Generates a Technology Landscape Memo for the keyword."""
    
    csv_dir = os.path.join(root_dir, "data", "processed")
    report_dir = os.path.join(root_dir, "outputs", "reports")
    
    os.makedirs(csv_dir, exist_ok=True)
    os.makedirs(report_dir, exist_ok=True)

    df['Lifecycle_Category'] = df['Raw_Status'].apply(categorize_status)
    
    # Extract the target info from the first row
    keyword = df['Keyword'].iloc[0]
    tech_category = df['Technology_Category'].iloc[0]
    
    safe_name = keyword.replace(" ", "_").replace("-", "_").lower()
    
    # Save CSV
    csv_path = os.path.join(csv_dir, f"tech_{safe_name}_landscape.csv")
    df.to_csv(csv_path, index=False)
    
    # Analytics
    total_apps = len(df)
    enforceable = len(df[df['Lifecycle_Category'] == 'Enforceable (Granted)'])
    abandoned = len(df[df['Lifecycle_Category'] == 'Abandoned (Wastage)'])
    pending = len(df[df['Lifecycle_Category'] == 'Pipeline (Active/Pending)'])
    
    resolved_cases = enforceable + abandoned
    allowance_rate = (enforceable / resolved_cases * 100) if resolved_cases > 0 else 0.0

    two_years_ago = pd.Timestamp.now() - pd.DateOffset(years=2)
    recent_filings = len(df[df['Filing_Date'] >= two_years_ago])

    # Generate the Memo
    report_path = os.path.join(report_dir, f"tech_{safe_name}_landscape_memo.txt")
    
    with open(report_path, 'w') as f:
        f.write("TECHNOLOGY LANDSCAPE SUMMARY\n")
        f.write("=" * 60 + "\n")
        f.write(f"SEARCH KEYWORD : '{keyword}'\n")
        f.write(f"TECH CATEGORY  : {tech_category}\n")
        f.write(f"REPORT DATE    : {datetime.now().strftime('%Y-%m-%d')}\n")
        f.write(f"SCOPE          : Title Search (Max Sample: 200 records)\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("1. TECHNOLOGY TRENDS & METRICS\n")
        f.write("-" * 60 + "\n")
        f.write(f"Total Applications Tracked    : {total_apps}\n")
        f.write(f"Granted / Enforceable Patents : {enforceable}  ({(enforceable/total_apps*100) if total_apps > 0 else 0:.1f}%)\n")
        f.write(f"Pending / Pipeline Patents    : {pending}  ({(pending/total_apps*100) if total_apps > 0 else 0:.1f}%)\n")
        f.write(f"Abandoned Patents             : {abandoned}  ({(abandoned/total_apps*100) if total_apps > 0 else 0:.1f}%)\n\n")
        
        f.write(f">> Historical Allowance Rate  : {allowance_rate:.1f}%\n")
        f.write(f">> R&D Heat (Filings last 2 yrs): {recent_filings} applications\n\n")

        f.write("2. RECENT INNOVATIONS IN THIS SPACE\n")
        f.write("-" * 60 + "\n")
        f.write("Top 5 most recent filings:\n")
        top_5 = df.head(5)
        for _, row in top_5.iterrows():
            date_str = row['Filing_Date'].strftime('%Y-%m-%d') if pd.notnull(row['Filing_Date']) else 'Unknown Date'
            f.write(f"  [{date_str}] {row['Title']}\n")
            f.write(f"      Status: {row['Lifecycle_Category']}\n")
        f.write("\n")

        f.write("3. PROSECUTING LAW FIRMS\n")
        f.write("-" * 60 + "\n")
        firm_counts = df['Law_Firm'].value_counts().head(10) # Top 10 firms
        for firm, count in firm_counts.items():
            percentage = (count/total_apps)*100
            f.write(f"  [{count:02d} cases | {percentage:04.1f}%] {firm}\n")
        
        f.write("\n4. DETAILED STATUS BREAKDOWN (USPTO RAW)\n")
        f.write("-" * 60 + "\n")
        status_counts = df['Raw_Status'].value_counts()
        for status, count in status_counts.items():
            f.write(f"  - {status}: {count}\n")
            
    print(f"📄 Generated Tech Memo: {os.path.basename(report_path)}")

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    root_dir = os.path.dirname(os.path.dirname(current_dir)) 
    
    raw_dir = os.path.join(root_dir, "data", "raw")
    
    # Note: Updated glob to catch the 'kw_*.json' files generated by your new fetcher
    json_files = glob.glob(os.path.join(raw_dir, "kw_*_raw.json"))
    
    if not json_files:
        print(f"❌ No keyword JSON files found in {raw_dir}. Run your fetcher first.")
        return

    print("Processing technology landscapes...\n")
    
    for json_path in json_files:
        df = load_and_flatten_data(json_path)
        
        if df is not None and not df.empty:
            generate_landscape_reports(df, root_dir) 
        else:
            print(f"⚠️ DataFrame is empty for {os.path.basename(json_path)}. Skipping.")

    print("\n✅ All Technology Landscape memos saved to 'outputs/reports/' folder!")

if __name__ == "__main__":
    main()