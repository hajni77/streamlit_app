# Bathroom Layout Generator API Documentation

This documentation describes how to integrate the bathroom layout generator API with your Flutter application.

## API Overview

The API provides bathroom layout generation services with optimized fixture placement based on various constraints. The API is built with FastAPI and provides JSON responses that can be easily consumed by Flutter applications.

## Base URL

When running locally:
```
http://localhost:8000
```

## Endpoints

### 1. Health Check

**Endpoint:** `GET /`

**Description:** Check if the API server is running.

**Response:**
```json
{
  "status": "ok",
  "message": "Bathroom Layout Generator API is running"
}
```

### 2. Generate Layout

**Endpoint:** `POST /api/generate`

**Description:** Generate a bathroom layout based on room dimensions and objects to place.

**Request Body:**

```json
{
  "room_width": 300,
  "room_depth": 240,
  "room_height": 280,
  "objects_to_place": [
    "toilet",
    "sink",
    "shower"
  ],
  "windows_doors": [
    {
      "name": "door",
      "position": [0, 120],
      "width": 80,
      "depth": 5,
      "height": 210,
      "wall": "left",
      "hinge": "bottom"
    },
    {
      "name": "window",
      "position": [100, 0],
      "width": 100,
      "depth": 5,
      "height": 120,
      "wall": "top"
    }
  ],
  "beam_width": 10
}
```

**Parameters:**
- `room_width` (required): Width of the bathroom in cm
- `room_depth` (required): Depth of the bathroom in cm
- `room_height` (optional, default: 280): Height of the bathroom in cm
- `objects_to_place` (required): Array of object types to place in the bathroom
- `windows_doors` (optional): Array of windows and doors in the bathroom
  - `name`: Name of the window/door (e.g., "door", "window")
  - `position`: [x, y] coordinates of the window/door in cm
  - `width`: Width of the window/door in cm
  - `depth`: Depth of the window/door in cm
  - `height`: Height of the window/door in cm (default: 210)
  - `wall`: Wall the window/door is placed on ("top", "bottom", "left", "right")
  - `hinge`: Side of the hinge for doors ("top", "bottom", "left", "right", optional)
- `beam_width` (optional, default: 10): Beam width for the search algorithm (higher = more thorough but slower)

**Response:**

```json
{
  "layout_id": "550e8400-e29b-41d4-a716-446655440000",
  "score": 78.5,
  "room_width": 300,
  "room_depth": 240,
  "room_height": 280,
  "objects": [
    {
      "object_type": "toilet",
      "position": [250, 60],
      "width": 40,
      "depth": 45,
      "height": 40,
      "wall": "bottom",
      "shadow": [30, 15, 15, 60]
    },
    {
      "object_type": "sink",
      "position": [120, 10],
      "width": 60,
      "depth": 45,
      "height": 85,
      "wall": "top",
      "shadow": [10, 10, 10, 60]
    },
    {
      "object_type": "shower",
      "position": [10, 120],
      "width": 80,
      "depth": 80,
      "height": 210,
      "wall": "top-left",
      "shadow": [15, 15, 15, 15]
    }
  ],
  "score_breakdown": {
    "no_overlap": 10,
    "wall_corner_constraints": 10,
    "corner_coverage": 5,
    "door_sink_toilet": 10,
    "corner_toilet": 0,
    "spacing": 8.3,
    "requested_objects": 10,
    "shadow_constraints": 10,
    "bathtub_placement": 0,
    "toilet_free_space": 8.5,
    "opposite_walls_distance": 10,
    "sink_opposite_door": 10
  },
  "processing_time": 1.25
}
```

**Error Responses:**

- 400 Bad Request: Could not generate a valid layout with the given constraints
- 500 Internal Server Error: Error in the layout generation process

### 3. Retrieve Layout

**Endpoint:** `GET /api/layout/{layout_id}`

**Description:** Retrieve a previously generated layout by ID.

**Parameters:**
- `layout_id` (path parameter): The unique ID of the layout to retrieve

**Response:** Same as the generate layout response

**Error Responses:**
- 404 Not Found: Layout with the given ID was not found

## Integration with Flutter

### Example HTTP Request with Dart

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

Future<Map<String, dynamic>> generateBathroomLayout({
  required double roomWidth,
  required double roomDepth,
  required List<String> objectsToPlace,
  List<Map<String, dynamic>> windowsDoors = const [],
}) async {
  final url = Uri.parse('http://localhost:8000/api/generate');
  
  final response = await http.post(
    url,
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'room_width': roomWidth,
      'room_depth': roomDepth,
      'objects_to_place': objectsToPlace,
      'windows_doors': windowsDoors,
    }),
  );
  
  if (response.statusCode == 200) {
    return jsonDecode(response.body);
  } else {
    throw Exception('Failed to generate layout: ${response.body}');
  }
}

// Example usage
void main() async {
  try {
    final layout = await generateBathroomLayout(
      roomWidth: 300,
      roomDepth: 240,
      objectsToPlace: ['toilet', 'sink', 'shower'],
      windowsDoors: [
        {
          'name': 'door',
          'position': [0, 120],
          'width': 80,
          'depth': 5,
          'height': 210,
          'wall': 'left',
          'hinge': 'bottom'
        }
      ],
    );
    
    print('Layout generated with ID: ${layout['layout_id']}');
    print('Layout score: ${layout['score']}');
    
    // Process the objects in the layout
    final objects = layout['objects'];
    for (var obj in objects) {
      print('${obj['object_type']} placed at position [${obj['position'][0]}, ${obj['position'][1]}]');
    }
  } catch (e) {
    print('Error: $e');
  }
}
```

### Available Object Types

The API supports the following bathroom fixtures:
- toilet
- sink
- double sink
- bathtub
- shower
- bidet
- toilet bidet (combination)
- washing machine

### Considerations for Flutter Integration

1. **Handle processing time**: The layout generation may take several seconds. Consider implementing a loading indicator in your Flutter UI.

2. **Error handling**: Be prepared to handle errors from the API, particularly when constraints make layout generation impossible.

3. **Caching**: The generated layouts are cached on the server for 24 hours. You can retrieve them using the layout ID without regenerating them.

4. **Visualization**: Use the object positions and dimensions to render the layout in your Flutter application.

5. **Network connectivity**: Ensure proper handling of network connectivity issues in your Flutter app.

## Running the API Server

To run the API server locally:

```bash
# Navigate to the project directory
cd path/to/project

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

This will start the API server at http://localhost:8000 with automatic reloading enabled.

## Authentication Endpoints

The API now supports user authentication for protected endpoints. Users can register, login, and access user-specific layouts.

### 4. User Registration

**Endpoint:** `POST /users/`

**Description:** Create a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "id": "user_id_123",
  "email": "user@example.com",
  "full_name": "John Doe",
  "disabled": false
}
```

### 5. User Login

**Endpoint:** `POST /token`

**Description:** Login and receive an access token for authenticated requests.

**Request Body (Form Data):**
```
username: user@example.com
password: securepassword
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "provider": "supabase"
}
```

### 6. Get Current User

**Endpoint:** `GET /users/me/`

**Description:** Get information about the currently authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": "user_id_123",
  "email": "user@example.com",
  "disabled": false
}
```

### 7. Generate Layout (Protected)

**Endpoint:** `POST /api/protected/generate`

**Description:** Generate a bathroom layout for authenticated users. The layout is automatically associated with the user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:** Same as the public `/api/generate` endpoint

**Response:** Same as the public endpoint, but the layout is saved with user association

### 8. Get User Layouts

**Endpoint:** `GET /api/protected/layouts/`

**Description:** Get all layouts created by the authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
[
  {
    "layout_id": "layout_123",
    "timestamp": "2025-09-30T10:00:00",
    "score": 78.5,
    "room_width": 300,
    "room_depth": 240,
    "room_height": 280
  },
  {
    "layout_id": "layout_456",
    "timestamp": "2025-09-29T15:30:00",
    "score": 82.3,
    "room_width": 350,
    "room_depth": 280,
    "room_height": 280
  }
]
```

### 9. Get User Layout by ID

**Endpoint:** `GET /api/protected/layout/{layout_id}`

**Description:** Retrieve a specific layout owned by the authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** Same as the generate layout response

**Error Responses:**
- 403 Forbidden: You don't have permission to access this layout
- 404 Not Found: Layout not found

### 10. Delete User Layout

**Endpoint:** `DELETE /api/protected/layout/{layout_id}`

**Description:** Delete a layout owned by the authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "message": "Layout layout_123 deleted successfully"
}
```

**Error Responses:**
- 403 Forbidden: You don't have permission to delete this layout
- 404 Not Found: Layout not found

### 11. Firebase Token Verification

**Endpoint:** `POST /auth/firebase/verify-token`

**Description:** Verify a Firebase ID token and get an API access token.

**Request Body:**
```json
{
  "idToken": "firebase_id_token_from_client"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user_id": "user_id_123",
  "email": "user@example.com"
}
```

## Authentication with Flutter

### Example: Login and Generate Layout

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class BathroomApiClient {
  final String baseUrl;
  String? _accessToken;
  
  BathroomApiClient({required this.baseUrl});
  
  // Login
  Future<bool> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/token'),
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: {
        'username': email,
        'password': password,
      },
    );
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      _accessToken = data['access_token'];
      
      // Save token to shared preferences
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('auth_token', _accessToken!);
      
      return true;
    }
    return false;
  }
  
  // Generate layout (authenticated)
  Future<Map<String, dynamic>> generateLayoutProtected({
    required double roomWidth,
    required double roomDepth,
    required List<String> objectsToPlace,
    List<Map<String, dynamic>> windowsDoors = const [],
  }) async {
    if (_accessToken == null) {
      throw Exception('Not authenticated');
    }
    
    final url = Uri.parse('$baseUrl/api/protected/generate');
    
    final response = await http.post(
      url,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $_accessToken',
      },
      body: jsonEncode({
        'room_width': roomWidth,
        'room_depth': roomDepth,
        'objects_to_place': objectsToPlace,
        'windows_doors': windowsDoors,
        'beam_width': 10,
      }),
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to generate layout: ${response.body}');
    }
  }
  
  // Get user layouts
  Future<List<dynamic>> getUserLayouts() async {
    if (_accessToken == null) {
      throw Exception('Not authenticated');
    }
    
    final response = await http.get(
      Uri.parse('$baseUrl/api/protected/layouts/'),
      headers: {
        'Authorization': 'Bearer $_accessToken',
      },
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to get layouts: ${response.body}');
    }
  }
}

// Example usage
void main() async {
  final client = BathroomApiClient(baseUrl: 'http://localhost:8000');
  
  // Login
  final success = await client.login('user@example.com', 'password');
  if (success) {
    print('Logged in successfully');
    
    // Generate a layout
    final layout = await client.generateLayoutProtected(
      roomWidth: 300,
      roomDepth: 240,
      objectsToPlace: ['toilet', 'sink', 'shower'],
    );
    
    print('Layout generated: ${layout['layout_id']}');
    
    // Get all user layouts
    final layouts = await client.getUserLayouts();
    print('User has ${layouts.length} layouts');
  }
}
```

### Authentication Best Practices

1. **Store tokens securely**: Use `shared_preferences` or `flutter_secure_storage` to store access tokens
2. **Handle token expiration**: Implement token refresh logic or re-authentication when tokens expire
3. **Use HTTPS in production**: Always use HTTPS for API requests in production environments
4. **Implement logout**: Clear stored tokens when users log out
