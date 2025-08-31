import frappe
import os
from frappe import _
from frappe.frappe.utils import get_site_url

def get_api_url(endpoint=None):
    """Return the full URL for an API endpoint"""
    site_url = get_site_url()
    base_url = f"{site_url}/api/method/inventory.api.routes"
    
    if endpoint:
        return f"{base_url}.{endpoint}"
    return base_url

def get_api_headers(token=None):
    """Return headers for API requests"""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    return headers

def update_jwt_settings(secret_key=None, expiry_time=None):
    """Update JWT settings in site_config.json"""
    from frappe.frappe.installer import update_site_config
    
    if secret_key:
        update_site_config("jwt_secret_key", secret_key)
    
    if expiry_time:
        update_site_config("jwt_expiry_time", expiry_time)
    
    frappe.msgprint(_("JWT settings updated successfully"))

@frappe.whitelist()
def get_swagger_definition():
    """Return Swagger/OpenAPI definition for mobile APIs"""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Inventory Mobile API",
            "description": "API for accessing Inventory app from mobile devices",
            "version": "1.0.0"
        },
        "servers": [
            {
                "url": get_api_url(),
                "description": "Production server"
            }
        ],
        "paths": {
            "/login": {
                "post": {
                    "summary": "Authenticate user and get JWT token",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "usr": {
                                            "type": "string",
                                            "description": "Username or email"
                                        },
                                        "pwd": {
                                            "type": "string",
                                            "description": "Password"
                                        }
                                    },
                                    "required": ["usr", "pwd"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Successful authentication",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
                                            },
                                            "token": {
                                                "type": "string"
                                            },
                                            "user": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {
                                                        "type": "string"
                                                    },
                                                    "email": {
                                                        "type": "string"
                                                    },
                                                    "roles": {
                                                        "type": "array",
                                                        "items": {
                                                            "type": "string"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "401": {
                            "description": "Authentication failed",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/validate_token": {
                "get": {
                    "summary": "Validate JWT token and get user info",
                    "security": [
                        {
                            "bearerAuth": []
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Token is valid",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "user": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {
                                                        "type": "string"
                                                    },
                                                    "email": {
                                                        "type": "string"
                                                    },
                                                    "roles": {
                                                        "type": "array",
                                                        "items": {
                                                            "type": "string"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "401": {
                            "description": "Invalid token",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/refresh_token": {
                "post": {
                    "summary": "Refresh JWT token",
                    "security": [
                        {
                            "bearerAuth": []
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Token refreshed successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
                                            },
                                            "token": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "401": {
                            "description": "Invalid token",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            
            # Master Data API paths
            "/list_customers": {
                "get": {
                    "summary": "Get a list of customers with optional search filter",
                    "security": [
                        {
                            "bearerAuth": []
                        }
                    ],
                    "parameters": [
                        {
                            "name": "search_text",
                            "in": "query",
                            "required": false,
                            "schema": {
                                "type": "string"
                            },
                            "description": "Text to search in customer names or IDs"
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "required": false,
                            "schema": {
                                "type": "integer",
                                "default": 20
                            },
                            "description": "Number of results to return (pagination)"
                        },
                        {
                            "name": "offset",
                            "in": "query",
                            "required": false,
                            "schema": {
                                "type": "integer",
                                "default": 0
                            },
                            "description": "Offset for pagination"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of customers",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "data": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "name": {
                                                            "type": "string"
                                                        },
                                                        "customer_name": {
                                                            "type": "string"
                                                        },
                                                        "customer_type": {
                                                            "type": "string"
                                                        },
                                                        "contact_number": {
                                                            "type": "string"
                                                        },
                                                        "email": {
                                                            "type": "string"
                                                        },
                                                        "wilaya": {
                                                            "type": "string"
                                                        },
                                                        "commune": {
                                                            "type": "string"
                                                        }
                                                    }
                                                }
                                            },
                                            "total": {
                                                "type": "integer"
                                            },
                                            "limit": {
                                                "type": "integer"
                                            },
                                            "offset": {
                                                "type": "integer"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/get_customer": {
                "get": {
                    "summary": "Get detailed customer information by ID",
                    "security": [
                        {
                            "bearerAuth": []
                        }
                    ],
                    "parameters": [
                        {
                            "name": "customer_id",
                            "in": "query",
                            "required": true,
                            "schema": {
                                "type": "string"
                            },
                            "description": "The ID of the customer"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Customer details",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "data": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {
                                                        "type": "string"
                                                    },
                                                    "customer_name": {
                                                        "type": "string"
                                                    },
                                                    "customer_type": {
                                                        "type": "string"
                                                    },
                                                    "contact_number": {
                                                        "type": "string"
                                                    },
                                                    "email": {
                                                        "type": "string"
                                                    },
                                                    "address": {
                                                        "type": "string"
                                                    },
                                                    "wilaya": {
                                                        "type": "string"
                                                    },
                                                    "commune": {
                                                        "type": "string"
                                                    },
                                                    "status": {
                                                        "type": "string"
                                                    },
                                                    "full_address": {
                                                        "type": "string"
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "404": {
                            "description": "Customer not found",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/list_items": {
                "get": {
                    "summary": "Get a list of items with optional search filter",
                    "security": [
                        {
                            "bearerAuth": []
                        }
                    ],
                    "parameters": [
                        {
                            "name": "search_text",
                            "in": "query",
                            "required": false,
                            "schema": {
                                "type": "string"
                            },
                            "description": "Text to search in item names or codes"
                        },
                        {
                            "name": "item_group",
                            "in": "query",
                            "required": false,
                            "schema": {
                                "type": "string"
                            },
                            "description": "Filter by item group"
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "required": false,
                            "schema": {
                                "type": "integer",
                                "default": 20
                            },
                            "description": "Number of results to return (pagination)"
                        },
                        {
                            "name": "offset",
                            "in": "query",
                            "required": false,
                            "schema": {
                                "type": "integer",
                                "default": 0
                            },
                            "description": "Offset for pagination"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of items",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "data": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "item_code": {
                                                            "type": "string"
                                                        },
                                                        "item_name": {
                                                            "type": "string"
                                                        },
                                                        "description": {
                                                            "type": "string"
                                                        },
                                                        "item_group": {
                                                            "type": "string"
                                                        },
                                                        "uom": {
                                                            "type": "string"
                                                        },
                                                        "disabled": {
                                                            "type": "boolean"
                                                        },
                                                        "batch_tracking": {
                                                            "type": "boolean"
                                                        },
                                                        "default_price": {
                                                            "type": "number"
                                                        },
                                                        "available_qty": {
                                                            "type": "number"
                                                        }
                                                    }
                                                }
                                            },
                                            "total": {
                                                "type": "integer"
                                            },
                                            "limit": {
                                                "type": "integer"
                                            },
                                            "offset": {
                                                "type": "integer"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/get_item": {
                "get": {
                    "summary": "Get detailed item information by item code",
                    "security": [
                        {
                            "bearerAuth": []
                        }
                    ],
                    "parameters": [
                        {
                            "name": "item_code",
                            "in": "query",
                            "required": true,
                            "schema": {
                                "type": "string"
                            },
                            "description": "The item code"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Item details",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "data": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {
                                                        "type": "string"
                                                    },
                                                    "item_name": {
                                                        "type": "string"
                                                    },
                                                    "description": {
                                                        "type": "string"
                                                    },
                                                    "item_group": {
                                                        "type": "string"
                                                    },
                                                    "unit_of_measurement": {
                                                        "type": "string"
                                                    },
                                                    "disabled": {
                                                        "type": "boolean"
                                                    },
                                                    "batch_tracking": {
                                                        "type": "boolean"
                                                    },
                                                    "default_price": {
                                                        "type": "number"
                                                    },
                                                    "available_qty": {
                                                        "type": "number"
                                                    },
                                                    "selling_prices": {
                                                        "type": "array",
                                                        "items": {
                                                            "type": "object",
                                                            "properties": {
                                                                "name": {
                                                                    "type": "string"
                                                                },
                                                                "price_list_rate": {
                                                                    "type": "number"
                                                                },
                                                                "customer": {
                                                                    "type": "string"
                                                                },
                                                                "valid_from": {
                                                                    "type": "string",
                                                                    "format": "date"
                                                                },
                                                                "valid_upto": {
                                                                    "type": "string",
                                                                    "format": "date"
                                                                }
                                                            }
                                                        }
                                                    },
                                                    "batches": {
                                                        "type": "array",
                                                        "items": {
                                                            "type": "object",
                                                            "properties": {
                                                                "name": {
                                                                    "type": "string"
                                                                },
                                                                "batch_number": {
                                                                    "type": "string"
                                                                },
                                                                "manufacturing_date": {
                                                                    "type": "string",
                                                                    "format": "date"
                                                                },
                                                                "expiry_date": {
                                                                    "type": "string",
                                                                    "format": "date"
                                                                },
                                                                "qty": {
                                                                    "type": "number"
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "404": {
                            "description": "Item not found",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/get_item_price": {
                "get": {
                    "summary": "Get pricing information for an item, with optional customer-specific pricing",
                    "security": [
                        {
                            "bearerAuth": []
                        }
                    ],
                    "parameters": [
                        {
                            "name": "item_code",
                            "in": "query",
                            "required": true,
                            "schema": {
                                "type": "string"
                            },
                            "description": "The item code"
                        },
                        {
                            "name": "customer",
                            "in": "query",
                            "required": false,
                            "schema": {
                                "type": "string"
                            },
                            "description": "The customer ID for customer-specific pricing"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Item pricing details",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "data": {
                                                "type": "object",
                                                "properties": {
                                                    "item_code": {
                                                        "type": "string"
                                                    },
                                                    "default_price": {
                                                        "type": "number"
                                                    },
                                                    "customer_price": {
                                                        "type": "number"
                                                    },
                                                    "has_customer_specific_price": {
                                                        "type": "boolean"
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/get_batch_list": {
                "get": {
                    "summary": "Get list of batches for an item with available quantity",
                    "security": [
                        {
                            "bearerAuth": []
                        }
                    ],
                    "parameters": [
                        {
                            "name": "item_code",
                            "in": "query",
                            "required": true,
                            "schema": {
                                "type": "string"
                            },
                            "description": "The item code"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of batches with available quantity",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "data": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "name": {
                                                            "type": "string"
                                                        },
                                                        "batch_number": {
                                                            "type": "string"
                                                        },
                                                        "manufacturing_date": {
                                                            "type": "string",
                                                            "format": "date"
                                                        },
                                                        "expiry_date": {
                                                            "type": "string",
                                                            "format": "date"
                                                        },
                                                        "available_qty": {
                                                            "type": "number"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/get_stock_balance": {
                "get": {
                    "summary": "Get stock balance for items",
                    "security": [
                        {
                            "bearerAuth": []
                        }
                    ],
                    "parameters": [
                        {
                            "name": "item_code",
                            "in": "query",
                            "required": false,
                            "schema": {
                                "type": "string"
                            },
                            "description": "Filter by specific item"
                        },
                        {
                            "name": "warehouse",
                            "in": "query",
                            "required": false,
                            "schema": {
                                "type": "string"
                            },
                            "description": "Filter by specific warehouse"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Stock balance information",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "data": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "item": {
                                                            "type": "string"
                                                        },
                                                        "item_name": {
                                                            "type": "string"
                                                        },
                                                        "uom": {
                                                            "type": "string"
                                                        },
                                                        "available_qty": {
                                                            "type": "number"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            
            # Delivery Note API paths
            "/list_delivery_notes": {
                "get": {
                    "summary": "Get a list of all delivery notes",
                    "security": [
                        {
                            "bearerAuth": []
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of delivery notes",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "data": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "name": {
                                                            "type": "string"
                                                        },
                                                        "customer": {
                                                            "type": "string"
                                                        },
                                                        "customer_name": {
                                                            "type": "string"
                                                        },
                                                        "delivery_date": {
                                                            "type": "string",
                                                            "format": "date"
                                                        },
                                                        "total_amount": {
                                                            "type": "number"
                                                        },
                                                        "docstatus": {
                                                            "type": "integer"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/get_delivery_note": {
                "get": {
                    "summary": "Get delivery note details by ID",
                    "security": [
                        {
                            "bearerAuth": []
                        }
                    ],
                    "parameters": [
                        {
                            "name": "delivery_note_id",
                            "in": "query",
                            "required": true,
                            "schema": {
                                "type": "string"
                            },
                            "description": "The ID of the delivery note"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Delivery note details",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "data": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {
                                                        "type": "string"
                                                    },
                                                    "customer": {
                                                        "type": "string"
                                                    },
                                                    "customer_name": {
                                                        "type": "string"
                                                    },
                                                    "delivery_date": {
                                                        "type": "string",
                                                        "format": "date"
                                                    },
                                                    "total_amount": {
                                                        "type": "number"
                                                    },
                                                    "docstatus": {
                                                        "type": "integer"
                                                    },
                                                    "items": {
                                                        "type": "array",
                                                        "items": {
                                                            "type": "object",
                                                            "properties": {
                                                                "item": {
                                                                    "type": "string"
                                                                },
                                                                "item_name": {
                                                                    "type": "string"
                                                                },
                                                                "quantity": {
                                                                    "type": "number"
                                                                },
                                                                "rate": {
                                                                    "type": "number"
                                                                },
                                                                "amount": {
                                                                    "type": "number"
                                                                },
                                                                "uom": {
                                                                    "type": "string"
                                                                },
                                                                "batch": {
                                                                    "type": "string"
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "404": {
                            "description": "Delivery note not found",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/create_delivery_note": {
                "post": {
                    "summary": "Create a new delivery note",
                    "security": [
                        {
                            "bearerAuth": []
                        }
                    ],
                    "requestBody": {
                        "required": true,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "customer": {
                                            "type": "string",
                                            "description": "Customer ID"
                                        },
                                        "delivery_date": {
                                            "type": "string",
                                            "format": "date",
                                            "description": "Delivery date (YYYY-MM-DD)"
                                        },
                                        "posting_time": {
                                            "type": "string",
                                            "format": "time",
                                            "description": "Posting time (HH:MM:SS)"
                                        },
                                        "sales_order": {
                                            "type": "string",
                                            "description": "Sales Order ID (optional)"
                                        },
                                        "remarks": {
                                            "type": "string",
                                            "description": "Remarks (optional)"
                                        },
                                        "auto_submit": {
                                            "type": "boolean",
                                            "description": "Auto submit document after creation"
                                        },
                                        "items": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "item": {
                                                        "type": "string",
                                                        "description": "Item ID"
                                                    },
                                                    "quantity": {
                                                        "type": "number",
                                                        "description": "Quantity"
                                                    },
                                                    "rate": {
                                                        "type": "number",
                                                        "description": "Rate"
                                                    },
                                                    "batch": {
                                                        "type": "string",
                                                        "description": "Batch ID (if applicable)"
                                                    },
                                                    "sales_order_item": {
                                                        "type": "string",
                                                        "description": "Sales Order Item ID (if applicable)"
                                                    }
                                                },
                                                "required": ["item", "quantity", "rate"]
                                            }
                                        }
                                    },
                                    "required": ["customer", "items"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Delivery note created successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
                                            },
                                            "data": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {
                                                        "type": "string"
                                                    },
                                                    "customer": {
                                                        "type": "string"
                                                    },
                                                    "delivery_date": {
                                                        "type": "string",
                                                        "format": "date"
                                                    },
                                                    "total_amount": {
                                                        "type": "number"
                                                    },
                                                    "docstatus": {
                                                        "type": "integer"
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request or validation error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/update_delivery_note": {
                "put": {
                    "summary": "Update an existing delivery note",
                    "security": [
                        {
                            "bearerAuth": []
                        }
                    ],
                    "parameters": [
                        {
                            "name": "delivery_note_id",
                            "in": "query",
                            "required": true,
                            "schema": {
                                "type": "string"
                            },
                            "description": "The ID of the delivery note to update"
                        }
                    ],
                    "requestBody": {
                        "required": true,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "delivery_date": {
                                            "type": "string",
                                            "format": "date",
                                            "description": "Delivery date (YYYY-MM-DD)"
                                        },
                                        "remarks": {
                                            "type": "string",
                                            "description": "Remarks"
                                        },
                                        "items": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {
                                                        "type": "string",
                                                        "description": "Row ID (for updating existing items)"
                                                    },
                                                    "item": {
                                                        "type": "string",
                                                        "description": "Item ID (for new items)"
                                                    },
                                                    "quantity": {
                                                        "type": "number",
                                                        "description": "Quantity"
                                                    },
                                                    "rate": {
                                                        "type": "number",
                                                        "description": "Rate"
                                                    },
                                                    "batch": {
                                                        "type": "string",
                                                        "description": "Batch ID"
                                                    }
                                                }
                                            }
                                        },
                                        "remove_items": {
                                            "type": "array",
                                            "items": {
                                                "type": "string"
                                            },
                                            "description": "Row IDs of items to remove"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Delivery note updated successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
                                            },
                                            "data": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {
                                                        "type": "string"
                                                    },
                                                    "customer": {
                                                        "type": "string"
                                                    },
                                                    "delivery_date": {
                                                        "type": "string",
                                                        "format": "date"
                                                    },
                                                    "total_amount": {
                                                        "type": "number"
                                                    },
                                                    "docstatus": {
                                                        "type": "integer"
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request or validation error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "404": {
                            "description": "Delivery note not found",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/delete_delivery_note": {
                "delete": {
                    "summary": "Delete a delivery note",
                    "security": [
                        {
                            "bearerAuth": []
                        }
                    ],
                    "parameters": [
                        {
                            "name": "delivery_note_id",
                            "in": "query",
                            "required": true,
                            "schema": {
                                "type": "string"
                            },
                            "description": "The ID of the delivery note to delete"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Delivery note deleted successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request or validation error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "404": {
                            "description": "Delivery note not found",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/submit_delivery_note": {
                "post": {
                    "summary": "Submit a delivery note",
                    "security": [
                        {
                            "bearerAuth": []
                        }
                    ],
                    "parameters": [
                        {
                            "name": "delivery_note_id",
                            "in": "query",
                            "required": true,
                            "schema": {
                                "type": "string"
                            },
                            "description": "The ID of the delivery note to submit"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Delivery note submitted successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
                                            },
                                            "data": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {
                                                        "type": "string"
                                                    },
                                                    "docstatus": {
                                                        "type": "integer"
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request or validation error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "404": {
                            "description": "Delivery note not found",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/cancel_delivery_note": {
                "post": {
                    "summary": "Cancel a delivery note",
                    "security": [
                        {
                            "bearerAuth": []
                        }
                    ],
                    "parameters": [
                        {
                            "name": "delivery_note_id",
                            "in": "query",
                            "required": true,
                            "schema": {
                                "type": "string"
                            },
                            "description": "The ID of the delivery note to cancel"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Delivery note cancelled successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
                                            },
                                            "data": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {
                                                        "type": "string"
                                                    },
                                                    "docstatus": {
                                                        "type": "integer"
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request or validation error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "404": {
                            "description": "Delivery note not found",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/get_delivery_notes_for_customer": {
                "get": {
                    "summary": "Get all delivery notes for a specific customer",
                    "security": [
                        {
                            "bearerAuth": []
                        }
                    ],
                    "parameters": [
                        {
                            "name": "customer_id",
                            "in": "query",
                            "required": true,
                            "schema": {
                                "type": "string"
                            },
                            "description": "The ID of the customer"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of delivery notes for the customer",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "data": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "name": {
                                                            "type": "string"
                                                        },
                                                        "delivery_date": {
                                                            "type": "string",
                                                            "format": "date"
                                                        },
                                                        "total_amount": {
                                                            "type": "number"
                                                        },
                                                        "docstatus": {
                                                            "type": "integer"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request or validation error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/get_delivery_note_items_from_sales_order": {
                "get": {
                    "summary": "Get items from a sales order to create a delivery note",
                    "security": [
                        {
                            "bearerAuth": []
                        }
                    ],
                    "parameters": [
                        {
                            "name": "sales_order_id",
                            "in": "query",
                            "required": true,
                            "schema": {
                                "type": "string"
                            },
                            "description": "The ID of the sales order"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Sales order items with details for delivery note creation",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "data": {
                                                "type": "object",
                                                "properties": {
                                                    "customer_info": {
                                                        "type": "object",
                                                        "properties": {
                                                            "customer": {
                                                                "type": "string"
                                                            },
                                                            "customer_name": {
                                                                "type": "string"
                                                            }
                                                        }
                                                    },
                                                    "items": {
                                                        "type": "array",
                                                        "items": {
                                                            "type": "object",
                                                            "properties": {
                                                                "item": {
                                                                    "type": "string"
                                                                },
                                                                "item_name": {
                                                                    "type": "string"
                                                                },
                                                                "quantity": {
                                                                    "type": "number"
                                                                },
                                                                "rate": {
                                                                    "type": "number"
                                                                },
                                                                "uom": {
                                                                    "type": "string"
                                                                },
                                                                "sales_order": {
                                                                    "type": "string"
                                                                },
                                                                "sales_order_item": {
                                                                    "type": "string"
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request or validation error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "404": {
                            "description": "Sales order not found",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        }
    } 