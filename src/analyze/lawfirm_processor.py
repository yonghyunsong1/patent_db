import json
import pandas as pd
import os
import glob
import spacy

# Load the NLP model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import subprocess
    import sys
    print("Downloading spaCy English model...")
    subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

# Define the Taxonomy
TAXONOMY = {
    'Systems Bio & Comp-Bio': [
        'bioinformatic', 'metabolomic', 'transcriptomic', 'genomic', 'sequencing', 
        'computational', 'in silico', 'structural biology', 'folding', 'docking', 
        'pathway', 'network', 'system biology', 'cryo-em', 'tomography', 'causal inference'
    ],
    'Medical Devices & Optics': [
        'image', 'imaging', 'optic', 'optical', 'microscopy', 'microscope', 'lens', 
        'ultrasound', 'mri', 'catheter', 'stent', 'implant', 'prosthesis', 'surgical', 
        'diagnostic', 'device', 'sensor', 'probe', 'noninvasive', 'fluidic', 'microfluidic'
    ],
    'Biotech & Pharma': [
        'antibody', 'antigen', 'protein', 'peptide', 'rna', 'dna', 'nucleic', 'cell', 
        'tissue', 'vaccine', 'therapy', 'therapeutic', 'pharmaceutical', 'molecule', 
        'assay', 'biomarker', 'enzyme', 'kinase', 'receptor', 'ligand', 'embryo', 
        'in vitro', 'crispr', 'gene'
    ],
    'Software & AI': [
        'machine learning', 'artificial intelligence', 'neural network', 'algorithm', 
        'software', 'data', 'interface', 'server', 'computing', 'database', 'predictive',
        'processor', 'cloud', 'model'
    ],
    'Hardware & Engineering': [
        'circuit', 'semiconductor', 'battery', 'display', 'antenna', 'voltage', 
        'memory', 'wireless', 'mechanical', 'motor'
    ],
    'Chemistry & Materials': [
        'composition', 'polymer', 'alloy', 'catalyst', 'coating', 'resin', 'fluid', 'chemical'
    ]
}

def classify_technology_nlp(title):
    if not isinstance(title, str) or title == 'Unknown':
        return 'Other / General'

    doc = nlp(title.lower())
    lemmas = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
    raw_text = doc.text
    scores = {category: 0 for category in TAXONOMY.keys()}

    for category, keywords in TAXONOMY.items():
        for keyword in keywords:
            if " " in keyword and keyword in raw_text:
                scores[category] += 2  
            elif keyword in lemmas:
                scores[category] += 1

    best_category = max(scores, key=scores.get)
    if scores[best_category] == 0:
        return 'Other / General'
    return best_category

def extract_corporate_client(doc):
    """
    Hybrid Extractor: Uses 'The Slash Trick' for new applications, 
    and falls back to JSON hunting for older/granted applications.
    """
    law_terms = ["LLP", "L.L.P", "ATTORNEY", "LAW FIRM", "LAW GROUP", "P.C.", "P.A.", "P.A", " ESQ", "COUNSEL", "IP "]
    
    def is_law_firm(name):
        return any(term in str(name).upper() for term in law_terms)

    # ---------------------------------------------------------
    # 1. THE SLASH TRICK (Highly effective for pending cases)
    # ---------------------------------------------------------
    address_bag = doc.get('correspondenceAddressBag', [])
    if isinstance(address_bag, list) and len(address_bag) > 0:
        name_line = str(address_bag[0].get('nameLineOneText', ''))
        if '/' in name_line:
            # Grab whatever is after the last slash (e.g. "Firm / Client Name")
            possible_client = name_line.split('/')[-1].strip()
            
            # Make sure the parsed client isn't just another part of the law firm name
            if len(possible_client) > 2 and not is_law_firm(possible_client):
                return possible_client.title()

    # ---------------------------------------------------------
    # 2. JSON HUNTER (For formally assigned older cases)
    # ---------------------------------------------------------
    candidates = []
    target_keys = {
        'organizationname', 'organizationnamestandardized', 
        'assigneeentityname', 'assigneeorganizationname',
        'assigneename', 'assigneenametext', 
        'applicantname', 'applicantnametext'
    }

    def hunt_json(node):
        if isinstance(node, dict):
            for k, v in node.items():
                k_lower = str(k).lower()
                if k_lower in target_keys:
                    if isinstance(v, str) and len(v.strip()) > 2:
                        candidates.append(v.strip())
                elif k_lower == 'namelineonetext': 
                    if isinstance(v, str) and len(v.strip()) > 2:
                        val = v.strip()
                        # Reject standard USPTO human name format "Smith, John" or "Smith; John"
                        if "," not in val and ";" not in val: 
                            candidates.append(val)
                if isinstance(v, (dict, list)):
                    hunt_json(v)
        elif isinstance(node, list):
            for item in node:
                hunt_json(item)

    # Only hunt in assignee/applicant bags to avoid reading inventor bags
    if 'assigneeBag' in doc: hunt_json(doc['assigneeBag'])
    if 'applicantBag' in doc: hunt_json(doc['applicantBag'])
    
    if 'applicationMetaData' in doc:
        meta = doc['applicationMetaData']
        if 'assigneeBag' in meta: hunt_json(meta['assigneeBag'])
        if 'applicantBag' in meta: hunt_json(meta['applicantBag'])

    valid = [c for c in candidates if not is_law_firm(c)]
    if not valid:
        return "Unknown"

    corp_indicators = [
        "INC", "LLC", "LTD", "CORP", "UNIVERSITY", "INSTITUTE", 
        "GMBH", "AG", "S.A.", "CO.", "PHARMA", "THERAPEUTICS", 
        "BIOSCIENCES", "TECHNOLOGIES", "BOARD OF", "TRUSTEES", "MEDICAL", "SYSTEMS"
    ]
    
    best_candidate = "Unknown"
    best_score = -1
    
    for c in list(set(valid)):
        score = len(c)
        c_upper = c.upper()
        if any(ind in c_upper for ind in corp_indicators):
            score += 500  
        if score > best_score:
            best_score = score
            best_candidate = c

    return best_candidate.title()

def categorize_status(status_string):
    status = str(status_string).upper()
    if 'PROVISIONAL' in status: return 'Provisional'
    elif 'PCT' in status or 'INTERNATIONAL' in status: return 'PCT (Intl)'
    elif 'PATENTED' in status or 'ISSUED' in status or 'ALLOW' in status: return 'Granted'
    elif 'ABANDON' in status: return 'Abandoned'
    else: return 'Pending'

def load_and_process_firm(json_path):
    with open(json_path, 'r') as f:
        raw_data = json.load(f)

    records = []
    for doc in raw_data:
        target_firm = doc.get('Search_Target_LawFirm', 'Unknown')
        meta = doc.get('applicationMetaData', {})
        
        title = meta.get('inventionTitle', 'Unknown')
        
        records.append({
            "Target_Firm": target_firm,
            "App_Number": doc.get('applicationNumberText', 'Unknown'),
            "Filing_Date": meta.get('filingDate', 'Unknown'),
            "Raw_Status": meta.get('applicationStatusDescriptionText', 'Unknown'),
            "Pipeline_Status": categorize_status(meta.get('applicationStatusDescriptionText', '')),
            "Title": title,
            "Tech_Area": classify_technology_nlp(title),
            "Corporate_Client": extract_corporate_client(doc)
        })

    df = pd.DataFrame(records)
    if not df.empty:
        df['Filing_Date'] = pd.to_datetime(df['Filing_Date'], errors='coerce')
        df = df.sort_values(by=['Filing_Date'], ascending=[False])
    return df

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    root_dir = os.path.dirname(os.path.dirname(current_dir)) 
    raw_dir = os.path.join(root_dir, "data", "raw")
    csv_dir = os.path.join(root_dir, "data", "processed")
    os.makedirs(csv_dir, exist_ok=True)

    json_files = glob.glob(os.path.join(raw_dir, "firm_*_raw.json"))
    
    if not json_files:
        print(f"❌ No law firm JSON files found. Run the fetcher first.")
        return

    print("Running NLP & Slash-Trick Assignee extraction...")
    for json_path in json_files:
        df = load_and_process_firm(json_path)
        if not df.empty:
            target_firm = df['Target_Firm'].iloc[0]
            safe_name = target_firm.replace(" ", "_").replace(",", "").replace("&", "and").lower()
            csv_path = os.path.join(csv_dir, f"firm_{safe_name}_profile.csv")
            df.to_csv(csv_path, index=False)
            print(f"✅ Processed data for: {target_firm}")

if __name__ == "__main__":
    main()