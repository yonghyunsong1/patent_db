import json
import pandas as pd
import os
import time
import re
from uspto_engine import USPTO_ODP_Engine

def build_smart_query(firm_name):
    """
    Constructs a robust Lucene query for the USPTO API.
    Converts "Amster Rothstein & Ebenstein" into:
    "Amster Rothstein & Ebenstein" OR correspondenceAddressBag:(Amster AND Rothstein AND Ebenstein)
    """
    # 1. Strip out legal entity suffixes and punctuation
    clean_name = re.sub(r'(?i)\b(LLP|LLC|P\.C\.|PC|PLLC|INC\.|LAW|FIRM|GROUP)\b', '', firm_name)
    clean_name = clean_name.replace('&', ' ').replace(',', ' ').replace('.', ' ')
    
    # 2. Extract core partner names/tokens, ignoring "and" / "the"
    tokens = [t.strip() for t in clean_name.split() if t.strip().lower() not in ['and', 'the']]
    
    exact_match = f'"{firm_name}"'
    
    # 3. If there are multiple names, build the "A AND B" address logic
    if len(tokens) > 1:
        and_str = " AND ".join(tokens)
        
        # Search exact match globally, OR ensure ALL partner names exist in the correspondence address
        smart_query = (
            f'{exact_match} OR '
            f'(correspondenceAddressBag.nameLineOneText:({and_str})) OR '
            f'(correspondenceAddressBag.nameLineTwoText:({and_str}))'
        )
        return smart_query
    else:
        # Single name firms (e.g., "Venable") just get the exact match
        return exact_match

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    root_dir = os.path.dirname(os.path.dirname(current_dir)) 
    
    config_path = os.path.join(root_dir, "configs", "law_firms.csv")
    
    try:
        firms_df = pd.read_csv(config_path)
        firms_df.columns = firms_df.columns.str.strip()
        firm_list = firms_df['law_firm_name'].dropna().tolist()
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

    for firm in firm_list:
        print(f"\n⚖️ Searching Law Firm: {firm}")
        
        # Use our new NLP query builder
        search_string = build_smart_query(firm)
        print(f"  -> Smart Query: {search_string}")
        
        # Pull up to 500 records
        docs = engine.execute_query(search_string=search_string, max_records=400)
        
        if not docs:
            print(f"  -> Skipping save, no data found for {firm}.")
            continue

        for doc in docs:
            doc['Search_Target_LawFirm'] = firm
            
        safe_filename = firm.replace(" ", "_").replace(",", "").replace("&", "and").lower()
        output_file = os.path.join(output_dir, f"firm_{safe_filename}_raw.json")
        
        with open(output_file, 'w') as f:
            json.dump(docs, f, indent=4)
            
        print(f"✅ Saved {len(docs)} records to {output_file}")
        total_records_pulled += len(docs)
        
        time.sleep(2) 
        
    print(f"\n🎉 Success! Downloaded {total_records_pulled} records across {len(firm_list)} law firms.")

if __name__ == "__main__":
    main()