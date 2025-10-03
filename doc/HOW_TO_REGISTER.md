# How to Register a User

## Prerequisites

1. **Start the API server**:
   ```bash
   python api.py
   ```
   
   The server should start at `http://localhost:8000`

2. **Configure Authentication Provider** (at least one):
   
   Create a `.env` file with your credentials:
   
   **Option A: Supabase** (Recommended)
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your_supabase_anon_key
   SECRET_KEY=your_random_secret_key_here
   ```
   
   **Option B: Firebase**
   ```env
   # Place firebase_credentials.json in the project root
   # OR use base64 encoded credentials:
   FIREBASE_CREDENTIALS_BASE64=your_base64_encoded_credentials
   SECRET_KEY=your_random_secret_key_here
   ```

## Method 1: Using the Registration Script (Easiest)

Run the interactive registration script:

```bash
python register_user_example.py
```

Follow the prompts:
- Enter your email
- Enter your password
- Enter your full name

The script will:
1. Register your account
2. Automatically log you in
3. Display your access token
4. Verify your account

## Method 2: Using cURL

```bash
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your_email@example.com",
    "password": "your_secure_password",
    "full_name": "Your Name"
  }'
```

**Expected Response:**
```json
{
  "id": "user_id_here",
  "email": "your_email@example.com",
  "full_name": "Your Name",
  "disabled": false
}
```

## Method 3: Using Python

```python
import requests

response = requests.post(
    "http://localhost:8000/users/",
    json={
        "email": "your_email@example.com",
        "password": "your_secure_password",
        "full_name": "Your Name"
    }
)

if response.status_code == 200:
    user = response.json()
    print(f"User registered: {user['email']}")
else:
    print(f"Error: {response.text}")
```

## Method 4: Using Postman/Thunder Client

1. **Create a new POST request**
2. **URL**: `http://localhost:8000/users/`
3. **Headers**:
   - `Content-Type: application/json`
4. **Body** (raw JSON):
   ```json
   {
     "email": "your_email@example.com",
     "password": "your_secure_password",
     "full_name": "Your Name"
   }
   ```
5. **Send** the request

## After Registration: Login

Once registered, you can login to get an access token:

```bash
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_email@example.com&password=your_secure_password"
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "provider": "supabase"
}
```

## Using Your Access Token

Include the token in the `Authorization` header for protected endpoints:

```bash
curl -X GET http://localhost:8000/users/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Or to generate a layout:

```bash
curl -X POST http://localhost:8000/api/protected/generate \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "my_layout_1",
    "room_width": 300,
    "room_depth": 240,
    "room_height": 280,
    "objects_to_place": ["toilet", "sink", "shower"],
    "windows_doors": [],
    "beam_width": 10
  }'
```

## Troubleshooting

### Error: "No authentication provider available"

**Solution**: Configure either Supabase or Firebase in your `.env` file.

### Error: "Cannot connect to API server"

**Solution**: Make sure the API is running:
```bash
python api.py
```

### Error: "User already exists"

**Solution**: The email is already registered. Try logging in instead or use a different email.

### Error: Import errors when starting API

**Solution**: Install missing dependencies:
```bash
pip install -r requirements.txt
```

If Supabase/Firebase imports fail, you can install them separately:
```bash
# For Supabase
pip install supabase

# For Firebase
pip install firebase-admin
```

### API starts but authentication doesn't work

**Solution**: Check your `.env` file configuration:
- Verify SUPABASE_URL and SUPABASE_KEY are correct
- Or verify firebase_credentials.json exists and is valid
- Ensure SECRET_KEY is set

## Testing Your Setup

Run the test script to verify everything works:

```bash
python test_auth_integration.py
```

This will test:
- ✓ API health check
- ✓ User registration
- ✓ Login
- ✓ Token validation
- ✓ Protected endpoints

## Quick Start Example

```bash
# 1. Start the API
python api.py

# 2. In another terminal, register a user
python register_user_example.py

# 3. Follow the prompts to create your account

# 4. Use the access token for authenticated requests
```

## Security Notes

- **Never share your access token** - it grants full access to your account
- **Use strong passwords** - at least 8 characters with mixed case, numbers, and symbols
- **Tokens expire** - default is 30 minutes, you'll need to login again
- **HTTPS in production** - always use HTTPS for production deployments
- **Secure storage** - store tokens securely in your client application

## Next Steps

After registration:
1. Generate bathroom layouts
2. Save and retrieve your layouts
3. View your layout history
4. Delete old layouts

See the API documentation for all available endpoints.
