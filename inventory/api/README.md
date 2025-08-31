# Inventory Mobile API

This module provides API endpoints for mobile applications to interact with the Inventory app.

## Setup

1. Install the required dependencies:

```bash
pip install PyJWT
```

2. Set the JWT configuration in your `site_config.json`:

```json
{
  "jwt_secret_key": "your-secure-secret-key",
  "jwt_expiry_time": 86400
}
```

- `jwt_secret_key`: A secure secret key for JWT token encryption
- `jwt_expiry_time`: Token expiry time in seconds (default: 86400 = 24 hours)

> **Note**: If you don't set these values, default values will be used. However, it's recommended to set your own secure key in production.

## API Endpoints

### Authentication

#### Login

- **URL**: `/api/method/inventory.api.routes.login`
- **Method**: `POST`
- **Auth Required**: No
- **Request Body**:
  ```json
  {
    "usr": "username",
    "pwd": "password"
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "message": "Authentication successful",
    "token": "JWT_TOKEN_HERE",
    "user": {
      "name": "User Full Name",
      "email": "user@example.com",
      "roles": ["Role1", "Role2"]
    }
  }
  ```

#### Validate Token

- **URL**: `/api/method/inventory.api.routes.validate_token`
- **Method**: `GET`
- **Auth Required**: Yes (Bearer Token)
- **Headers**:
  ```
  Authorization: Bearer JWT_TOKEN_HERE
  ```
- **Response**:
  ```json
  {
    "success": true,
    "user": {
      "name": "User Full Name",
      "email": "user@example.com",
      "roles": ["Role1", "Role2"]
    }
  }
  ```

#### Refresh Token

- **URL**: `/api/method/inventory.api.routes.refresh_token`
- **Method**: `POST`
- **Auth Required**: Yes (Bearer Token, can be expired)
- **Headers**:
  ```
  Authorization: Bearer JWT_TOKEN_HERE
  ```
- **Response**:
  ```json
  {
    "success": true,
    "message": "Token refreshed",
    "token": "NEW_JWT_TOKEN_HERE"
  }
  ```

## Documentation

View the API documentation at:

```
https://your-site.com/api_docs
```

## Creating New API Endpoints

To create a new secure API endpoint, follow this pattern:

```python
@frappe.whitelist()
def my_secure_api():
    # Validate token first
    from inventory.api.auth import authenticate_request
    auth_response = authenticate_request()
    if not auth_response.get("success"):
        return auth_response
    
    # Your API logic here
    return {"success": True, "data": "Your data"}
```

Then add it to the routes.py file:

```python
@frappe.whitelist()
def my_secure_api(*args, **kwargs):
    """Wrapper for your_module.my_secure_api to match REST API conventions"""
    from your_module import my_secure_api
    return my_secure_api()
```

## Testing

You can test the API using tools like Postman or curl:

```bash
# Login and get token
curl -X POST \
  'https://your-site.com/api/method/inventory.api.routes.login' \
  -H 'Content-Type: application/json' \
  -d '{"usr":"admin","pwd":"admin"}'

# Use token for authenticated requests
curl -X GET \
  'https://your-site.com/api/method/inventory.api.routes.validate_token' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
``` 