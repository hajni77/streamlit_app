import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

/// Bathroom Layout API Authentication Service
/// 
/// This service handles authentication with the Bathroom Layout Generator API.
/// It works alongside your existing AWS Cognito authentication.
/// 
/// Usage:
/// 1. After AWS Cognito login succeeds
/// 2. Call loginToBathroomApi() to get API access token
/// 3. Store token for use with bathroom layout endpoints

class BathroomApiAuthService {
  // API Configuration
  static const String baseUrl = 'http://YOUR_SERVER_IP:8000'; // Change to your server IP
  
  String? _accessToken;
  String? _userEmail;
  
  // Singleton pattern
  static final BathroomApiAuthService _instance = BathroomApiAuthService._internal();
  factory BathroomApiAuthService() => _instance;
  BathroomApiAuthService._internal();
  
  /// Get current access token
  String? get accessToken => _accessToken;
  
  /// Check if user is authenticated with bathroom API
  bool get isAuthenticated => _accessToken != null;
  
  /// Get user email
  String? get userEmail => _userEmail;
  
  /// Initialize service and load saved token
  Future<void> init() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _accessToken = prefs.getString('bathroom_api_token');
      _userEmail = prefs.getString('bathroom_api_email');
    } catch (e) {
      print('Error loading saved token: $e');
    }
  }
  
  /// Login to Bathroom API
  /// Call this after successful AWS Cognito login
  Future<bool> loginToBathroomApi({
    required String email,
    required String password,
  }) async {
    try {
      print('🔐 Logging into Bathroom API...');
      
      final response = await http.post(
        Uri.parse('$baseUrl/token'),
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: {
          'username': email,
          'password': password,
        },
      ).timeout(const Duration(seconds: 10));
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _accessToken = data['access_token'];
        _userEmail = email;
        
        // Save token to shared preferences
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('bathroom_api_token', _accessToken!);
        await prefs.setString('bathroom_api_email', email);
        
        print('✅ Bathroom API login successful');
        print('Provider: ${data['provider']}');
        return true;
      } else if (response.statusCode == 401) {
        print('❌ Invalid credentials for Bathroom API');
        // User might not be registered in Bathroom API yet
        // Try to register them
        return await _registerAndLogin(email, password);
      } else {
        print('❌ Login failed: ${response.statusCode}');
        print('Response: ${response.body}');
        return false;
      }
    } catch (e) {
      print('❌ Login error: $e');
      return false;
    }
  }
  
  /// Register user in Bathroom API if they don't exist
  Future<bool> _registerAndLogin(String email, String password) async {
    try {
      print('📝 Registering user in Bathroom API...');
      
      final response = await http.post(
        Uri.parse('$baseUrl/users/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email,
          'password': password,
          'full_name': email.split('@')[0], // Use email prefix as name
        }),
      ).timeout(const Duration(seconds: 10));
      
      if (response.statusCode == 200) {
        print('✅ User registered successfully');
        // Now try to login
        return await loginToBathroomApi(email: email, password: password);
      } else {
        print('❌ Registration failed: ${response.statusCode}');
        print('Response: ${response.body}');
        return false;
      }
    } catch (e) {
      print('❌ Registration error: $e');
      return false;
    }
  }
  
  /// Get current user info from Bathroom API
  Future<Map<String, dynamic>?> getUserInfo() async {
    if (_accessToken == null) {
      print('❌ Not authenticated');
      return null;
    }
    
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/users/me/'),
        headers: {'Authorization': 'Bearer $_accessToken'},
      ).timeout(const Duration(seconds: 10));
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        print('❌ Failed to get user info: ${response.statusCode}');
        return null;
      }
    } catch (e) {
      print('❌ Error getting user info: $e');
      return null;
    }
  }
  
  /// Generate bathroom layout (protected endpoint)
  Future<Map<String, dynamic>?> generateLayout({
    required double roomWidth,
    required double roomDepth,
    required double roomHeight,
    required List<String> objectsToPlace,
    List<Map<String, dynamic>> windowsDoors = const [],
    int beamWidth = 10,
  }) async {
    if (_accessToken == null) {
      print('❌ Not authenticated. Please login first.');
      return null;
    }
    
    try {
      print('🏗️ Generating bathroom layout...');
      
      final layoutId = 'layout_${DateTime.now().millisecondsSinceEpoch}';
      
      final response = await http.post(
        Uri.parse('$baseUrl/api/protected/generate'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $_accessToken',
        },
        body: jsonEncode({
          'id': layoutId,
          'room_width': roomWidth,
          'room_depth': roomDepth,
          'room_height': roomHeight,
          'objects_to_place': objectsToPlace,
          'windows_doors': windowsDoors,
          'beam_width': beamWidth,
        }),
      ).timeout(const Duration(seconds: 30));
      
      if (response.statusCode == 200) {
        final layout = jsonDecode(response.body);
        print('✅ Layout generated successfully');
        print('Layout ID: ${layout['layout_id']}');
        print('Score: ${layout['score']}');
        return layout;
      } else if (response.statusCode == 401) {
        print('❌ Authentication expired. Please login again.');
        await logout();
        return null;
      } else {
        print('❌ Failed to generate layout: ${response.statusCode}');
        print('Response: ${response.body}');
        return null;
      }
    } catch (e) {
      print('❌ Error generating layout: $e');
      return null;
    }
  }
  
  /// Get all user's layouts
  Future<List<dynamic>?> getUserLayouts() async {
    if (_accessToken == null) {
      print('❌ Not authenticated');
      return null;
    }
    
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/protected/layouts/'),
        headers: {'Authorization': 'Bearer $_accessToken'},
      ).timeout(const Duration(seconds: 10));
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        print('❌ Failed to get layouts: ${response.statusCode}');
        return null;
      }
    } catch (e) {
      print('❌ Error getting layouts: $e');
      return null;
    }
  }
  
  /// Get specific layout by ID
  Future<Map<String, dynamic>?> getLayout(String layoutId) async {
    if (_accessToken == null) {
      print('❌ Not authenticated');
      return null;
    }
    
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/protected/layout/$layoutId'),
        headers: {'Authorization': 'Bearer $_accessToken'},
      ).timeout(const Duration(seconds: 10));
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        print('❌ Failed to get layout: ${response.statusCode}');
        return null;
      }
    } catch (e) {
      print('❌ Error getting layout: $e');
      return null;
    }
  }
  
  /// Delete a layout
  Future<bool> deleteLayout(String layoutId) async {
    if (_accessToken == null) {
      print('❌ Not authenticated');
      return false;
    }
    
    try {
      final response = await http.delete(
        Uri.parse('$baseUrl/api/protected/layout/$layoutId'),
        headers: {'Authorization': 'Bearer $_accessToken'},
      ).timeout(const Duration(seconds: 10));
      
      if (response.statusCode == 200) {
        print('✅ Layout deleted successfully');
        return true;
      } else {
        print('❌ Failed to delete layout: ${response.statusCode}');
        return false;
      }
    } catch (e) {
      print('❌ Error deleting layout: $e');
      return false;
    }
  }
  
  /// Logout from Bathroom API
  Future<void> logout() async {
    try {
      if (_accessToken != null) {
        await http.post(
          Uri.parse('$baseUrl/logout'),
          headers: {'Authorization': 'Bearer $_accessToken'},
        ).timeout(const Duration(seconds: 5));
      }
    } catch (e) {
      print('Error during logout: $e');
    } finally {
      _accessToken = null;
      _userEmail = null;
      
      // Clear saved token
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove('bathroom_api_token');
      await prefs.remove('bathroom_api_email');
      
      print('✅ Logged out from Bathroom API');
    }
  }
}

/// Extension to integrate with your existing login screen
extension BathroomApiIntegration on BathroomApiAuthService {
  /// Call this after successful AWS Cognito login
  /// This will automatically register/login to Bathroom API
  Future<bool> syncWithAwsLogin({
    required String email,
    required String password,
  }) async {
    print('🔄 Syncing with Bathroom API...');
    final success = await loginToBathroomApi(
      email: email,
      password: password,
    );
    
    if (success) {
      print('✅ Bathroom API sync successful');
    } else {
      print('⚠️ Bathroom API sync failed (non-critical)');
    }
    
    return success;
  }
}
