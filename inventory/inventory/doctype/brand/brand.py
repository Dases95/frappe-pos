# Copyright (c) 2023, Inventory App and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Brand(Document):
	def validate(self):
		"""Validate the Brand document"""
		self.validate_brand_name()
		
	def validate_brand_name(self):
		"""Validate that brand name is unique and not empty"""
		if not self.brand_name:
			frappe.throw("Brand Name is required")
			
		if self.brand_name != self.brand_name.strip():
			self.brand_name = self.brand_name.strip()
			
		# Check for duplicate brand names
		existing = frappe.db.exists("Brand", {
			"brand_name": self.brand_name,
			"name": ["!=", self.name]
		})
		
		if existing:
			frappe.throw(f"Brand with name '{self.brand_name}' already exists")
	
	def before_save(self):
		"""Actions to perform before saving the document"""
		if not self.name:
			self.name = self.brand_name
			
	def on_update(self):
		"""Actions to perform after updating the document"""
		# Update all items that reference this brand
		self.update_item_references()
		
	def update_item_references(self):
		"""Update items that reference this brand"""
		items = frappe.get_all("Item", 
			filters={"brand": self.name},
			fields=["name"]
		)
		
		for item in items:
			# Clear cache for items to reflect brand changes
			frappe.clear_cache(doctype="Item", name=item.name)
			
	def on_trash(self):
		"""Actions to perform before deleting the document"""
		# Check if any items are using this brand
		items_using_brand = frappe.get_all("Item", 
			filters={"brand": self.name},
			fields=["name", "item_name"]
		)
		
		if items_using_brand:
			item_names = [item.item_name for item in items_using_brand]
			frappe.throw(
				f"Cannot delete Brand '{self.brand_name}' as it is being used by items: {', '.join(item_names)}"
			)


@frappe.whitelist()
def get_brands():
	"""Get all active brands for dropdown/select options"""
	brands = frappe.get_all("Brand",
		filters={"disabled": 0},
		fields=["name", "brand_name", "description"],
		order_by="brand_name"
	)
	return brands


@frappe.whitelist()
def get_items_by_brand(brand):
	"""Get all items belonging to a specific brand"""
	if not brand:
		return []
		
	items = frappe.get_all("Item",
		filters={"brand": brand, "disabled": 0},
		fields=["name", "item_name", "item_code", "standard_rate"],
		order_by="item_name"
	)
	return items


@frappe.whitelist()
def get_brand_statistics(brand):
	"""Get statistics for a specific brand"""
	if not brand:
		return {}
		
	# Count total items
	total_items = frappe.db.count("Item", {"brand": brand, "disabled": 0})
	
	# Count active items (is_sales_item = 1)
	active_items = frappe.db.count("Item", {
		"brand": brand, 
		"disabled": 0, 
		"is_sales_item": 1
	})
	
	# Get average selling rate
	avg_rate = frappe.db.sql("""
		SELECT AVG(standard_rate) as avg_rate
		FROM `tabItem`
		WHERE brand = %s AND disabled = 0 AND standard_rate > 0
	""", brand)[0][0] or 0
	
	return {
		"total_items": total_items,
		"active_items": active_items,
		"average_selling_rate": avg_rate
	}