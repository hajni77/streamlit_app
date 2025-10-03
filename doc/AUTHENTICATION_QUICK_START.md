# Authentication Quick Start Guide

This guide provides a quick overview of how to use the authentication system in the Bathroom Layout Generator API.

## Setup

1. **Configure Environment Variables**

Create a `.env` file based on `.env.example`:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_key

# JWT Configuration
SECRET_KEY=your_secure_random_string
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

2. **Install Dependencies**

```bash
pip install -r requirements.txt
```

3. **Start the API Server**

```bash
python api.py
```

The server will start at `http://localhost:8000`

## API Endpoints Overview

### Public Endpoints (No Authentication Required)

- `GET /` - Health check
- `POST /api/generate` - Generate bathroom layout (public)
- `GET /api/layout/{layout_id}` - Get layout by ID

### Authentication Endpoints

- `POST /users/` - Register new user
- `POST /token` - Login and get access token
- `GET /users/me/` - Get current user info
- `POST /auth/firebase/verify-token` - Verify Firebase token

### Protected Endpoints (Authentication Required)

- `POST /api/protected/generate` - Generate layout (user-specific)
- `GET /api/protected/layouts/` - Get all user layouts
- `GET /api/protected/layout/{layout_id}` - Get specific user layout
- `DELETE /api/protected/layout/{layout_id}` - Delete user layout
- `GET /api/protected/layouts/public/` - Get public templates

## Quick Examples

### 1. Register a New User

```bash
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword",
    "full_name": "John Doe"
  }'
```

### 2. Login and Get Token

```bash
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=securepassword"
```

Response:
```json
{
  "access_token": "eyJ0eXAi...",
  "token_type": "bearer",
  "provider": "supabase"
}
```

### 3. Generate Layout (Authenticated)

```bash
curl -X POST http://localhost:8000/api/protected/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "id": "my_layout_123",
    "room_width": 300,
    "room_depth": 240,
    "room_height": 280,
    "objects_to_place": ["toilet", "sink", "shower"],
    "windows_doors": [],
    "beam_width": 10
  }'
```

### 4. Get All User Layouts

```bash
curl -X GET http://localhost:8000/api/protected/layouts/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 5. Delete a Layout

```bash
curl -X DELETE http://localhost:8000/api/protected/layout/my_layout_123 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Python Client Example

```python
import requests

class BathroomApiClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.token = None
    
    def login(self, email, password):
        """Login and store access token"""
        response = requests.post(
            f"{self.base_url}/token",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            return True
        return False
    
    def generate_layout(self, room_width, room_depth, objects):
        """Generate a bathroom layout"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        data = {
            "id": f"layout_{room_width}x{room_depth}",
            "room_width": room_width,
            "room_depth": room_depth,
            "room_height": 280,
            "objects_to_place": objects,
            "windows_doors": [],
            "beam_width": 10
        }
        response = requests.post(
            f"{self.base_url}/api/protected/generate",
            json=data,
            headers=headers
        )
        return response.json()
    
    def get_my_layouts(self):
        """Get all layouts for current user"""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            f"{self.base_url}/api/protected/layouts/",
            headers=headers
        )
        return response.json()

# Usage
client = BathroomApiClient()
if client.login("user@example.com", "password"):
    layout = client.generate_layout(300, 240, ["toilet", "sink", "shower"])
    print(f"Generated layout: {layout['layout_id']}")
    
    layouts = client.get_my_layouts()
    print(f"Total layouts: {len(layouts)}")
```

## Flutter Client Example

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class BathroomApiClient {
  final String baseUrl;
  String? _token;
  
  BathroomApiClient(this.baseUrl);
  
  Future<bool> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/token'),
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: {'username': email, 'password': password},
    );
    
    if (response.statusCode == 200) {
      _token = jsonDecode(response.body)['access_token'];
      return true;
    }
    return false;
  }
  
  Future<Map<String, dynamic>> generateLayout({
    required double roomWidth,
    required double roomDepth,
    required List<String> objects,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/protected/generate'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $_token',
      },
      body: jsonEncode({
        'id': 'layout_${DateTime.now().millisecondsSinceEpoch}',
        'room_width': roomWidth,
        'room_depth': roomDepth,
        'room_height': 280,
        'objects_to_place': objects,
        'windows_doors': [],
        'beam_width': 10,
      }),
    );
    
    return jsonDecode(response.body);
  }
  
  Future<List<dynamic>> getMyLayouts() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/protected/layouts/'),
      headers: {'Authorization': 'Bearer $_token'},
    );
    
    return jsonDecode(response.body);
  }
}

// Usage
void main() async {
  final client = BathroomApiClient('http://localhost:8000');
  
  if (await client.login('user@example.com', 'password')) {
    final layout = await client.generateLayout(
      roomWidth: 300,
      roomDepth: 240,
      objects: ['toilet', 'sink', 'shower'],
    );
    print('Generated: ${layout['layout_id']}');
    
    final layouts = await client.getMyLayouts();
    print('Total layouts: ${layouts.length}');
  }
}
```

## Testing

Run the comprehensive test suite:

```bash
python test_auth_integration.py
```

This will test:
- ✓ User registration
- ✓ Login/authentication
- ✓ Token validation
- ✓ Protected endpoints
- ✓ Layout generation
- ✓ User layout management
- ✓ Unauthorized access prevention

## Troubleshooting

### "Not authenticated" error
- Ensure you're including the `Authorization: Bearer <token>` header
- Check that your token hasn't expired (default: 30 minutes)
- Verify the token format is correct

### "Could not validate credentials"
- Your token may be expired - login again to get a new token
- Ensure the SECRET_KEY in `.env` matches the one used to generate the token

### "You don't have permission to access this layout"
- The layout belongs to another user
- Use the public endpoint or generate your own layout

### Supabase/Firebase connection errors
- Verify your `.env` configuration
- Check that credentials are valid
- Ensure the authentication service is accessible

## Security Best Practices

1. **Never commit `.env` files** - Use `.env.example` as a template
2. **Use HTTPS in production** - Never send tokens over HTTP
3. **Rotate SECRET_KEY regularly** - Invalidates all existing tokens
4. **Implement token refresh** - For long-running applications
5. **Store tokens securely** - Use secure storage in mobile apps
6. **Validate input** - API validates all inputs, but client-side validation improves UX

## Next Steps

- See `API_DOCUMENTATION.md` for complete API reference
- See `USER_API_README.md` for detailed authentication documentation
- Check `flutter_integration_example/auth_example.dart` for full Flutter example
- Review `example_protected_api.py` for integration patterns
