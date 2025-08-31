import frappe
from frappe.utils.fixtures import sync_fixtures

DEFAULT_UOMS = [
    {
        "doctype": "UOM",
        "uom_name": "Kilogram",
        "uom_abbreviation": "KG",
        "description": "Standard unit for measuring mass"
    },
    {
        "doctype": "UOM",
        "uom_name": "Gram",
        "uom_abbreviation": "G",
        "description": "One thousandth of a kilogram"
    },
    {
        "doctype": "UOM",
        "uom_name": "Liter",
        "uom_abbreviation": "L",
        "description": "Standard unit for measuring volume"
    },
    {
        "doctype": "UOM",
        "uom_name": "Milliliter",
        "uom_abbreviation": "ML",
        "description": "One thousandth of a liter"
    },
    {
        "doctype": "UOM",
        "uom_name": "Unit",
        "uom_abbreviation": "EA",
        "description": "Each or individual item"
    },
    {
        "doctype": "UOM",
        "uom_name": "Box",
        "uom_abbreviation": "BX",
        "description": "Container for packaging multiple items"
    },
    {
        "doctype": "UOM",
        "uom_name": "Piece",
        "uom_abbreviation": "PC",
        "description": "Individual piece or part"
    },
    {
        "doctype": "UOM",
        "uom_name": "Dozen",
        "uom_abbreviation": "DOZ",
        "description": "Twelve units"
    }
]

def setup_uom_fixtures():
    # Create default UOMs
    for uom_data in DEFAULT_UOMS:
        if not frappe.db.exists("UOM", {"uom_name": uom_data["uom_name"]}):
            try:
                uom = frappe.new_doc("UOM")
                uom.update(uom_data)
                uom.insert(ignore_permissions=True)
                print(f"Created UOM: {uom.uom_name}")
            except Exception as e:
                print(f"Error creating UOM {uom_data['uom_name']}: {e}")

if __name__ == "__main__":
    frappe.init(site="stock.localhost")
    frappe.connect()
    setup_uom_fixtures()
    frappe.db.commit()
    print("UOM fixtures installed successfully!") 