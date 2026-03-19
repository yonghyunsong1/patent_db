import json
import pandas as pd
import os
import time
from uspto_engine import USPTO_ODP_Engine

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    root_dir = os.path.dirname(os.path.dirname(current_dir)) 
    
    config_path = os.path.join(root_dir, "configs", "cpc_codes.csv")
    try:
        cpc_df = pd.read_csv(config_path, comment='#')   
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

    for index, row in cpc_df.iterrows():
        cpc_code = row['cpc_code'].strip()
        description = row['description'].strip()
        
        print(f"\n🔬 Searching Tech Class: {cpc_code} ({description})")
        
        safe_cpc = cpc_code.replace("/", "\\/")
        search_string = safe_cpc

        # We pull 500 records here to get a true industry landscape
        docs = engine.execute_query(search_string=search_string, max_records=500)
        
        if not docs:
            print(f"  -> Skipping save, no data found.")
            continue

        # Tag the data
        for doc in docs:
            doc['Search_Target_Technology'] = description
            doc['CPC_Code'] = cpc_code
            
        # Create a clean filename (e.g., "A61D 19/00" -> "a61d_19_00")
        safe_filename = cpc_code.replace(" ", "_").replace("/", "_").lower()
        output_file = os.path.join(output_dir, f"cpc_{safe_filename}_raw.json")
        
        with open(output_file, 'w') as f:
            json.dump(docs, f, indent=4)
            
        print(f"✅ Saved {len(docs)} records to {output_file}")
        time.sleep(2) 

if __name__ == "__main__":
    main()