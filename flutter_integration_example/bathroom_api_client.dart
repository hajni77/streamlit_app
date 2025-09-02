import 'dart:convert';
import 'package:http/http.dart' as http;

/// API client for the Bathroom Layout Generator API
class BathroomApiClient {
  final String baseUrl;
  
  /// Constructor requires a base URL for the API
  BathroomApiClient({required this.baseUrl});
  
  /// Check API server health
  Future<bool> checkHealth() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/'));
      final data = jsonDecode(response.body);
      return data['status'] == 'ok';
    } catch (e) {
      print('Error checking API health: $e');
      return false;
    }
  }
  
  /// Generate a bathroom layout
  /// Returns the layout data if successful, throws an exception otherwise
  Future<Map<String, dynamic>> generateLayout({
    required double roomWidth,
    required double roomDepth,
    double roomHeight = 280,
    required List<String> objectsToPlace,
    List<Map<String, dynamic>> windowsDoors = const [],
    int beamWidth = 10,
  }) async {
    final requestBody = {
      'room_width': roomWidth,
      'room_depth': roomDepth,
      'room_height': roomHeight,
      'objects_to_place': objectsToPlace,
      'windows_doors': windowsDoors,
      'beam_width': beamWidth,
    };
    
    final response = await http.post(
      Uri.parse('$baseUrl/api/generate'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(requestBody),
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      final errorData = jsonDecode(response.body);
      throw Exception(errorData['detail'] ?? 'Failed to generate layout');
    }
  }
  
  /// Retrieve a previously generated layout by ID
  Future<Map<String, dynamic>> getLayout(String layoutId) async {
    final response = await http.get(Uri.parse('$baseUrl/api/layout/$layoutId'));
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      final errorData = jsonDecode(response.body);
      throw Exception(errorData['detail'] ?? 'Failed to retrieve layout');
    }
  }
}
