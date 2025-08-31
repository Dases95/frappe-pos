#!/usr/bin/env python
import json
import os
import sys
from collections import OrderedDict

# Path to the downloaded data
REPO_PATH = os.path.expanduser("~/Workspace/frappe15/temp_data/DZ_cities-master")
AR_CITIES_PATH = os.path.join(REPO_PATH, "Ar", "cities.json")
# Output paths defined relative to the script's location for better portability
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(SCRIPT_DIR, "fixtures")
WILAYA_OUTPUT_PATH = os.path.join(FIXTURES_DIR, "wilaya.json")
COMMUNE_OUTPUT_PATH = os.path.join(FIXTURES_DIR, "commune.json")

def extract_data(input_path=None):
    """Extract Wilaya and Commune data from the Arabic cities.json file
    
    Args:
        input_path: Optional custom path to the cities.json file
    """
    # Make sure fixtures directory exists
    os.makedirs(FIXTURES_DIR, exist_ok=True)
    
    # Use provided input path or default
    cities_path = input_path if input_path else AR_CITIES_PATH
    print(f"Reading data from {cities_path}")
    
    if not os.path.exists(cities_path):
        print(f"ERROR: File not found at {cities_path}")
        print("Please download the data first or provide the correct path.")
        return False
    
    # Load data from JSON file
    try:
        with open(cities_path, 'r', encoding='utf-8') as f:
            cities_data = json.load(f)
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON format in {cities_path}")
        return False
    except Exception as e:
        print(f"ERROR: Failed to read data from {cities_path}: {e}")
        return False
    
    # Extract unique wilayas
    wilayas = {}
    for commune in cities_data.get("communes", []):
        code_w = commune.get("codeW", "")
        wilaya_name = commune.get("wilaya", "")
        
        if code_w and wilaya_name and code_w != "" and wilaya_name != "اختر ولاية":
            wilayas[code_w] = wilaya_name
    
    if not wilayas:
        print("ERROR: No Wilaya data extracted. Check the input file structure.")
        return False
    
    # Create wilaya fixtures
    wilaya_fixtures = []
    for code, name in wilayas.items():
        wilaya_fixtures.append({
            "doctype": "Wilaya",
            "name": name,
            "wilaya_name": name,
            "wilaya_code": code,
            "description": f"ولاية {name}"
        })
    
    # Sort by wilaya_code
    wilaya_fixtures = sorted(wilaya_fixtures, key=lambda x: x["wilaya_code"])
    
    # Create commune fixtures
    commune_fixtures = []
    for commune in cities_data.get("communes", []):
        code_w = commune.get("codeW", "")
        wilaya_name = commune.get("wilaya", "")
        code_c = commune.get("codeC", "")
        commune_name = commune.get("baladiya", "")
        
        if (code_w and wilaya_name and code_c and commune_name and 
            code_w != "" and wilaya_name != "اختر ولاية" and 
            commune_name != "إختر بلدية"):
            commune_fixtures.append({
                "doctype": "Commune",
                "name": commune_name,
                "commune_name": commune_name,
                "commune_code": code_c,
                "wilaya": wilaya_name,
                "description": f"بلدية {commune_name} - ولاية {wilaya_name}"
            })
    
    if not commune_fixtures:
        print("ERROR: No Commune data extracted. Check the input file structure.")
        return False
    
    # Sort by commune_code
    commune_fixtures = sorted(commune_fixtures, key=lambda x: x["commune_code"])
    
    # Write to fixture files
    try:
        with open(WILAYA_OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(wilaya_fixtures, f, ensure_ascii=False, indent=2)
        
        with open(COMMUNE_OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(commune_fixtures, f, ensure_ascii=False, indent=2)
        
        print(f"Extracted {len(wilaya_fixtures)} wilayas and {len(commune_fixtures)} communes")
        print(f"Wilaya fixtures written to {WILAYA_OUTPUT_PATH}")
        print(f"Commune fixtures written to {COMMUNE_OUTPUT_PATH}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to write fixture files: {e}")
        return False

if __name__ == "__main__":
    # Allow custom input path from command line
    input_path = sys.argv[1] if len(sys.argv) > 1 else None
    success = extract_data(input_path)
    if success:
        print("Data extraction completed successfully!")
    else:
        print("Data extraction failed.")
        sys.exit(1) 