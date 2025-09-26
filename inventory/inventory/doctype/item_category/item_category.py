# Copyright (c) 2023, Inventory App and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ItemCategory(Document):
	def validate(self):
		"""Validate the Item Category document"""
		self.validate_category_name()
		
	def validate_category_name(self):
		"""Validate that category name is unique and not empty"""
		if not self.category_name:
			frappe.throw("Category Name is required")
			
		if self.category_name != self.category_name.strip():
			self.category_name = self.category_name.strip()
			
		# Check for duplicate category names
		existing = frappe.db.exists("Item Category", {
			"category_name": self.category_name,
			"name": ["!=", self.name]
		})
		
		if existing:
			frappe.throw(f"Item Category with name '{self.category_name}' already exists")
	
	def before_save(self):
		"""Actions to perform before saving the document"""
		if not self.name:
			self.name = self.category_name
			
	def on_update(self):
		"""Actions to perform after updating the document"""
		# Update all items that reference this category
		self.update_item_references()
		
	def update_item_references(self):
		"""Update items that reference this category"""
		items = frappe.get_all("Item", 
			filters={"item_category": self.name},
			fields=["name"]
		)
		
		for item in items:
			# Clear cache for items to reflect category changes
			frappe.clear_cache(doctype="Item", name=item.name)
			
	def on_trash(self):
		"""Actions to perform before deleting the document"""
		# Check if any items are using this category
		items_using_category = frappe.get_all("Item", 
			filters={"item_category": self.name},
			fields=["name", "item_name"]
		)
		
		if items_using_category:
			item_names = [item.item_name for item in items_using_category]
			frappe.throw(
				f"Cannot delete Item Category '{self.category_name}' as it is being used by items: {', '.join(item_names)}"
			)


@frappe.whitelist()
def get_item_categories():
	"""Get all active item categories for dropdown/select options"""
	categories = frappe.get_all("Item Category",
		filters={"disabled": 0},
		fields=["name", "category_name", "description"],
		order_by="category_name"
	)
	return categories


@frappe.whitelist()
def get_items_by_category(category):
	"""Get all items belonging to a specific category"""
	if not category:
		return []
		
	items = frappe.get_all("Item",
		filters={"item_category": category, "disabled": 0},
		fields=["name", "item_name", "item_code", "standard_rate"],
		order_by="item_name"
	)
	return items