import json
import pandas as pd
import os
import time
from uspto_engine import USPTO_ODP_Engine

def main():
    # Bulletproof Pathing: Finds the root 'patent_db' folder dynamically
    current_dir = os.path.dirname(os.path.abspath(__file__)) # gets src/fetch/
    root_dir = os.path.dirname(os.path.dirname(current_dir)) # goes up to patent_db/
    
    config_path = os.path.join(root_dir, "configs", "companies.csv")
    
    try:
        companies_df = pd.read_csv(config_path)
        companies_df.columns = companies_df.columns.str.strip()
        company_list = companies_df['company_name'].dropna().tolist()
    except FileNotFoundError:
        print(f"❌ Error: Could not find {config_path}.")
        return

    try:
        engine = USPTO_ODP_Engine()
    except ValueError as e:
        print(e)
        return

    output_dir = os.path.join(root_dir, "data", "raw")
    os.makedirs(output_dir, exist_ok=True)

    total_records_pulled = 0

    for company in company_list:
        print(f"\n🏢 Searching Company: {company}")
        search_string = f'"{company}"'
        
        # Pull up to 200 records per company
        docs = engine.execute_query(search_string=search_string, max_records=200)
        
        if not docs:
            print(f"  -> Skipping save, no data found for {company}.")
            continue

        # Tag the data with the company name
        for doc in docs:
            doc['Search_Target_Company'] = company
            
        # Create a clean, filesystem-safe filename (e.g., "Eikon Therapeutics" -> "company_eikon_therapeutics_raw.json")
        safe_filename = company.replace(" ", "_").replace(",", "").lower()
        output_file = os.path.join(output_dir, f"company_{safe_filename}_raw.json")
        
        # Save this specific company's data immediately
        with open(output_file, 'w') as f:
            json.dump(docs, f, indent=4)
            
        print(f"✅ Saved {len(docs)} records to {output_file}")
        total_records_pulled += len(docs)
        
        time.sleep(2) # Respect the rate limits between companies
        
    print(f"\n🎉 Success! Downloaded a total of {total_records_pulled} records across {len(company_list)} companies.")

if __name__ == "__main__":
    main()