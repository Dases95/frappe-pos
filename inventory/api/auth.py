import frappe
import jwt
import datetime
import os
import secrets
from frappe import _

# Configuration with fallbacks
def get_jwt_settings():
    """Get JWT settings from site_config.json with fallbacks"""
    # Try to get settings from site_config.json
    secret_key = frappe.conf.get("jwt_secret_key")
    expiry_time = frappe.conf.get("jwt_expiry_time")
    
    # If settings not found, use defaults
    if not secret_key:
        # In production, use a random key and log it
        if frappe.local.flags.in_production:
            secret_key = secrets.token_hex(32)
            frappe.log_error(f"JWT_SECRET_KEY not set in site_config.json. Using temporary key: {secret_key}")
        else:
            # For development, use a fixed key
            secret_key = "your-secret-key-for-development-only"
    
    if not expiry_time:
        # Default: 24 hours
        expiry_time = 24 * 60 * 60
    
    return {
        "secret_key": secret_key,
        "algorithm": "HS256",
        "expiry_time": expiry_time
    }

# Get JWT settings
JWT_SETTINGS = get_jwt_settings()

@frappe.whitelist(allow_guest=True)
def login():
    """
    API endpoint for mobile login
    
    Request format:
    {
        "usr": "username",
        "pwd": "password"
    }
    
    Response format:
    {
        "success": true,
        "message": "Authentication successful",
        "token": "JWT_TOKEN_HERE",
        "user": {
            "name": "User full name",
            "email": "user@example.com",
            "roles": ["Role1", "Role2"]
        }
    }
    """
    try:
        # Get login credentials from request
        usr = frappe.form_dict.usr
        pwd = frappe.form_dict.pwd
        
        if not usr or not pwd:
            return generate_error_response("Username and password are required")
        
        # Authenticate user
        frappe.local.login_manager.authenticate(usr, pwd)
        if frappe.local.login_manager.user == "Guest":
            frappe.local.response["http_status_code"] = 401
            return generate_error_response("Invalid username or password")
        
        frappe.local.login_manager.post_login()
        
        # Generate JWT token
        user = frappe.get_doc("User", frappe.session.user)
        token_payload = {
            "user": user.name,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_SETTINGS["expiry_time"]),
            "iat": datetime.datetime.utcnow(),
            "roles": [role.role for role in user.roles]
        }
        
        token = jwt.encode(token_payload, JWT_SETTINGS["secret_key"], algorithm=JWT_SETTINGS["algorithm"])
        
        # Return success response with token
        return {
            "success": True,
            "message": "Authentication successful",
            "token": token,
            "user": {
                "name": user.full_name,
                "email": user.email,
                "roles": [role.role for role in user.roles]
            }
        }
    except Exception as e:
        frappe.log_error(f"Mobile API Login Error: {str(e)}")
        return generate_error_response(f"Login failed: {str(e)}")

@frappe.whitelist()
def validate_token():
    """Validate JWT token and return user information"""
    try:
        auth_header = frappe.request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            frappe.local.response["http_status_code"] = 401
            return generate_error_response("Authorization header missing or invalid")
        
        token = auth_header.split(" ")[1]
        
        try:
            payload = jwt.decode(token, JWT_SETTINGS["secret_key"], algorithms=[JWT_SETTINGS["algorithm"]])
            user = frappe.get_doc("User", payload["user"])
            
            return {
                "success": True,
                "user": {
                    "name": user.full_name,
                    "email": user.email,
                    "roles": [role.role for role in user.roles]
                }
            }
        except jwt.ExpiredSignatureError:
            frappe.local.response["http_status_code"] = 401
            return generate_error_response("Token has expired")
        except jwt.InvalidTokenError:
            frappe.local.response["http_status_code"] = 401
            return generate_error_response("Invalid token")
    except Exception as e:
        frappe.log_error(f"Token Validation Error: {str(e)}")
        frappe.local.response["http_status_code"] = 500
        return generate_error_response(f"Error validating token: {str(e)}")

@frappe.whitelist()
def refresh_token():
    """Refresh JWT token"""
    try:
        auth_header = frappe.request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            frappe.local.response["http_status_code"] = 401
            return generate_error_response("Authorization header missing or invalid")
        
        token = auth_header.split(" ")[1]
        
        try:
            # Decode token without verifying expiration
            payload = jwt.decode(
                token, 
                JWT_SETTINGS["secret_key"], 
                algorithms=[JWT_SETTINGS["algorithm"]],
                options={"verify_exp": False}
            )
            
            # Generate new token
            user = frappe.get_doc("User", payload["user"])
            new_payload = {
                "user": user.name,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_SETTINGS["expiry_time"]),
                "iat": datetime.datetime.utcnow(),
                "roles": [role.role for role in user.roles]
            }
            
            new_token = jwt.encode(new_payload, JWT_SETTINGS["secret_key"], algorithm=JWT_SETTINGS["algorithm"])
            
            return {
                "success": True,
                "message": "Token refreshed",
                "token": new_token
            }
        except jwt.InvalidTokenError:
            frappe.local.response["http_status_code"] = 401
            return generate_error_response("Invalid token")
    except Exception as e:
        frappe.log_error(f"Token Refresh Error: {str(e)}")
        frappe.local.response["http_status_code"] = 500
        return generate_error_response(f"Error refreshing token: {str(e)}")

def generate_error_response(message):
    """Generate a standardized error response"""
    return {
        "success": False,
        "message": message
    }

def authenticate_request():
    """Middleware to authenticate requests with JWT token
    
    Usage: Add this to the beginning of any API endpoint that needs authentication
    
    Example:
    ```
    @frappe.whitelist()
    def my_secure_api():
        # Validate token first
        auth_response = authenticate_request()
        if not auth_response.get("success"):
            return auth_response
        
        # Your API logic here
        return {"success": True, "data": "Your data"}
    ```
    """
    try:
        auth_header = frappe.request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            frappe.local.response["http_status_code"] = 401
            return generate_error_response("Authorization header missing or invalid")
        
        token = auth_header.split(" ")[1]
        
        try:
            payload = jwt.decode(token, JWT_SETTINGS["secret_key"], algorithms=[JWT_SETTINGS["algorithm"]])
            frappe.session.user = payload["user"]
            return {"success": True}
        except jwt.ExpiredSignatureError:
            frappe.local.response["http_status_code"] = 401
            return generate_error_response("Token has expired")
        except jwt.InvalidTokenError:
            frappe.local.response["http_status_code"] = 401
            return generate_error_response("Invalid token")
    except Exception as e:
        frappe.log_error(f"Authentication Error: {str(e)}")
        frappe.local.response["http_status_code"] = 500
        return generate_error_response(f"Error authenticating request: {str(e)}")

