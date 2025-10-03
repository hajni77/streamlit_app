# User Authentication API

This module provides authentication capabilities for the Bathroom Layout Generator API, enabling secure access to user-specific layouts and features.

## Features

- User registration and login
- JWT token-based authentication
- Integration with Supabase and Firebase authentication services
- Protected API endpoints for user-specific data
- Token verification and validation

## Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables in `.env` file:
   ```
   # Firebase Configuration
   FIREBASE_CREDENTIALS_BASE64=your_base64_encoded_credentials
   # OR place firebase_credentials.json in the root directory

   # Supabase Configuration
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key

   # JWT Configuration
   SECRET_KEY=your_secret_key_for_jwt_encoding
   ```

3. Import and use the authentication module in your FastAPI application:
   ```python
   from fastapi import FastAPI, Depends
   from user_api import setup_user_api_routes, User, get_current_active_user

   app = FastAPI()
   setup_user_api_routes(app)

   @app.get("/protected-endpoint/")
   def protected_endpoint(current_user: User = Depends(get_current_active_user)):
       return {"message": f"Hello, {current_user.email}!"}
   ```

## Authentication Flow

### User Registration
```
POST /users/
{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe"
}
```

### User Login
```
POST /token
Form data:
  username: user@example.com
  password: securepassword
```
Response:
```json
{
  "access_token": "eyJ0eXAi...",
  "token_type": "bearer",
  "provider": "supabase"
}
```

### Accessing Protected Endpoints
Include the token in the Authorization header:
```
Authorization: Bearer eyJ0eXAi...
```

### Firebase Token Verification
If using Firebase authentication directly from a client:
```
POST /auth/firebase/verify-token
{
  "idToken": "firebase_id_token_from_client"
}
```

## Integration with Bathroom Layout Generator

The authentication system integrates with the bathroom layout generator to:

1. Associate layouts with specific users
2. Allow users to save and retrieve their layouts
3. Restrict access to private layouts
4. Enable sharing of layouts between users

See `example_protected_api.py` for examples of how to integrate authentication with the bathroom layout generator API.

## Security Notes

1. In production, always use HTTPS for API endpoints
2. Store JWT SECRET_KEY securely and rotate regularly
3. Set appropriate token expiration times
4. Consider implementing refresh tokens for longer sessions
5. Implement rate limiting for authentication endpoints

## Usage with Flutter

For Flutter clients, you can use either:

1. The `firebase_auth` package for Firebase authentication
2. The `supabase_flutter` package for Supabase authentication

Example Flutter code for authentication is provided in the `flutter_integration_example` directory.
