# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class POSShortcut(Document):
	def validate(self):
		self.validate_shortcut_key()
		self.validate_item_details()
		self.validate_unique_shortcut()

	def validate_shortcut_key(self):
		"""Validate shortcut key format"""
		if not self.shortcut_key:
			frappe.throw(_("Shortcut key is required"))
		
		# Allow alphanumeric keys and function keys
		valid_keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
					 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12']
		
		if self.shortcut_key not in valid_keys:
			frappe.throw(_("Shortcut key must be a number (0-9) or function key (F1-F12)"))

	def validate_item_details(self):
		"""Validate item details for product shortcuts"""
		if self.shortcut_type == "Product":
			if not self.item_code:
				frappe.throw(_("Item Code is required for Product shortcuts"))
			
			# Auto-fill item name if not provided
			if not self.item_name and self.item_code:
				item_name = frappe.db.get_value("Item", self.item_code, "item_name")
				if item_name:
					self.item_name = item_name

	def validate_unique_shortcut(self):
		"""Ensure shortcut key is unique"""
		existing = frappe.db.exists("POS Shortcut", {
			"shortcut_key": self.shortcut_key,
			"is_active": 1,
			"name": ["!=", self.name]
		})
		
		if existing:
			frappe.throw(_("Shortcut key '{0}' is already in use").format(self.shortcut_key))

	@frappe.whitelist()
	def get_shortcut_action(self):
		"""Get the action details for this shortcut"""
		if self.shortcut_type == "Product":
			return {
				"type": "product",
				"item_code": self.item_code,
				"item_name": self.item_name
			}
		elif self.shortcut_type == "Function":
			return {
				"type": "function",
				"action": self.action_type
			}
		elif self.shortcut_type == "Payment":
			return {
				"type": "payment",
				"method": self.shortcut_name
			}
		
		return None


@frappe.whitelist()
def get_all_shortcuts():
	"""Get all active shortcuts"""
	shortcuts = frappe.get_all("POS Shortcut", 
		filters={"is_active": 1},
		fields=["shortcut_name", "shortcut_type", "shortcut_key", "item_code", "item_name", "action_type"],
		order_by="shortcut_key"
	)
	
	# Organize shortcuts by type
	organized = {
		"products": [],
		"functions": [],
		"payments": []
	}
	
	for shortcut in shortcuts:
		if shortcut.shortcut_type == "Product":
			organized["products"].append(shortcut)
		elif shortcut.shortcut_type == "Function":
			organized["functions"].append(shortcut)
		elif shortcut.shortcut_type == "Payment":
			organized["payments"].append(shortcut)
	
	return organized


@frappe.whitelist()
def create_default_shortcuts():
	"""Create default shortcuts for new installations"""
	default_shortcuts = [
		# Function shortcuts
		{"shortcut_name": "New Sale", "shortcut_type": "Function", "shortcut_key": "F1", "action_type": "New Sale"},
		{"shortcut_name": "Clear Cart", "shortcut_type": "Function", "shortcut_key": "F2", "action_type": "Clear Cart"},
		{"shortcut_name": "Print Receipt", "shortcut_type": "Function", "shortcut_key": "F3", "action_type": "Print Receipt"},
		{"shortcut_name": "Close Session", "shortcut_type": "Function", "shortcut_key": "F4", "action_type": "Close Session"},
		{"shortcut_name": "Toggle Language", "shortcut_type": "Function", "shortcut_key": "F5", "action_type": "Toggle Language"},
		
		# Payment shortcuts
		{"shortcut_name": "Cash", "shortcut_type": "Payment", "shortcut_key": "1"},
		{"shortcut_name": "Card", "shortcut_type": "Payment", "shortcut_key": "2"},
		{"shortcut_name": "Bank Transfer", "shortcut_type": "Payment", "shortcut_key": "3"},
	]
	
	for shortcut_data in default_shortcuts:
		if not frappe.db.exists("POS Shortcut", {"shortcut_key": shortcut_data["shortcut_key"]}):
			shortcut = frappe.new_doc("POS Shortcut")
			shortcut.update(shortcut_data)
			shortcut.insert()
	
	frappe.msgprint(_("Default shortcuts created successfully!")) 