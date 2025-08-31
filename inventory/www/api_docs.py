import frappe
import os
from frappe import _
from frappe.website.utils import get_html_content_based_on_type

def get_context(context):
    """API Documentation context"""
    context.title = _("Mobile API Documentation")
    context.no_cache = 1
    
    # Get the HTML content of the swagger documentation
    api_dir = frappe.get_app_path("inventory", "api")
    swagger_html_path = os.path.join(api_dir, "swagger.html")
    
    if os.path.exists(swagger_html_path):
        with open(swagger_html_path, "r") as f:
            context.api_docs_html = f.read()
    else:
        context.api_docs_html = "<div class='alert alert-danger'>API documentation not found</div>"
    
    return context 