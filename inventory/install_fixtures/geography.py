import frappe
import json
import os
import shutil
from frappe.utils.fixtures import sync_fixtures

# Import our permanently stored geographical data
from inventory.data.algeria_geography import WILAYAS, COMMUNES

def setup_geography_fixtures():
    """Set up geography fixtures for Algeria (Wilayas and Communes)"""
    print("Setting up geography fixtures...")
    
    # Make sure DocTypes are created before trying to load fixtures
    ensure_doctypes_exist()
    
    # First try to use Frappe's built-in fixture syncing mechanism
    try:
        print("Trying built-in fixture syncing mechanism...")
        ensure_fixture_files_exist()
        sync_fixtures("inventory")
        print("Built-in fixture syncing completed successfully.")
    except Exception as e:
        print(f"Error during built-in fixture sync: {e}")
        print("Falling back to manual fixture loading...")
        # Fall back to manual method if sync_fixtures fails
        setup_wilayas_manually()
        setup_communes_manually()
    
    print("Geography fixtures installation completed.")

def ensure_doctypes_exist():
    """Ensure the DocTypes exist before trying to load fixtures"""
    # Check if Wilaya DocType exists
    if not frappe.db.exists("DocType", "Wilaya"):
        print("Wilaya DocType doesn't exist. Please install/migrate the app first.")
    
    # Check if Commune DocType exists
    if not frappe.db.exists("DocType", "Commune"):
        print("Commune DocType doesn't exist. Please install/migrate the app first.")

def ensure_fixture_files_exist():
    """Ensure fixture files exist in the fixtures directory using our embedded data"""
    fixture_dir = frappe.get_app_path("inventory", "fixtures")
    
    # Create fixtures directory if it doesn't exist
    os.makedirs(fixture_dir, exist_ok=True)
    
    # Create wilaya.json fixture file
    wilaya_file = os.path.join(fixture_dir, "wilaya.json")
    with open(wilaya_file, 'w', encoding='utf-8') as f:
        json.dump(WILAYAS, f, ensure_ascii=False, indent=2)
    
    # Create commune.json fixture file
    commune_file = os.path.join(fixture_dir, "commune.json")
    with open(commune_file, 'w', encoding='utf-8') as f:
        json.dump(COMMUNES, f, ensure_ascii=False, indent=2)
    
    print(f"Fixture files created: {wilaya_file}, {commune_file}")

def setup_wilayas_manually():
    """Set up Wilaya (province) fixtures manually using embedded data"""
    print("Manually installing Wilaya records...")
    
    # Create each Wilaya
    wilayas_created = 0
    for data in WILAYAS:
        if not frappe.db.exists("Wilaya", {"wilaya_name": data["wilaya_name"]}):
            try:
                wilaya = frappe.new_doc("Wilaya")
                # Copy only the required fields
                wilaya.wilaya_name = data["wilaya_name"]
                wilaya.wilaya_code = data["wilaya_code"]
                wilaya.description = data["description"]
                wilaya.insert(ignore_permissions=True)
                wilayas_created += 1
                if wilayas_created % 10 == 0:
                    print(f"Created {wilayas_created} Wilayas so far...")
            except Exception as e:
                print(f"Error creating Wilaya {data['wilaya_name']}: {e}")
    
    print(f"Successfully created {wilayas_created} Wilayas.")

def setup_communes_manually():
    """Set up Commune (municipality) fixtures manually using embedded data"""
    print("Manually installing Commune records...")
    
    # Create each Commune
    communes_created = 0
    for data in COMMUNES:
        if not frappe.db.exists("Commune", {"commune_name": data["commune_name"]}):
            try:
                commune = frappe.new_doc("Commune")
                # Copy only the required fields
                commune.commune_name = data["commune_name"]
                commune.commune_code = data["commune_code"]
                commune.wilaya = data["wilaya"]
                commune.description = data["description"]
                commune.insert(ignore_permissions=True)
                communes_created += 1
                if communes_created % 100 == 0:
                    print(f"Created {communes_created} Communes so far...")
            except Exception as e:
                print(f"Error creating Commune {data['commune_name']}: {e}")
    
    print(f"Successfully created {communes_created} Communes.")

# Command to run this script directly
def execute_from_command_line():
    """Function to run this script directly from bench execute"""
    setup_geography_fixtures()
    print("Geography fixtures installed successfully!")

if __name__ == "__main__":
    frappe.init(site="your_site_name")
    frappe.connect()
    setup_geography_fixtures()
    frappe.db.commit()
    print("Geography fixtures installed successfully!") 