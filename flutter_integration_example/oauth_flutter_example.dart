import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:firebase_auth/firebase_auth.dart' as firebase_auth;
import 'package:google_sign_in/google_sign_in.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

/// OAuth Authentication Example for Bathroom Layout API
/// 
/// This demonstrates how to use OAuth providers (Google, GitHub) 
/// with both Supabase and Firebase.

// ============================================================================
// SUPABASE OAUTH EXAMPLE
// ============================================================================

class SupabaseOAuthExample {
  final SupabaseClient supabase;
  final String apiBaseUrl;
  
  SupabaseOAuthExample({
    required this.supabase,
    required this.apiBaseUrl,
  });
  
  /// Sign in with Google using Supabase
  Future<String?> signInWithGoogle(BuildContext context) async {
    try {
      // Start OAuth flow
      final response = await supabase.auth.signInWithOAuth(
        Provider.google,
        redirectTo: 'your-app://callback', // Configure in Supabase dashboard
      );
      
      if (response) {
        // Wait for the auth state change
        final session = supabase.auth.currentSession;
        if (session != null) {
          // Get the access token
          final accessToken = session.accessToken;
          print('✅ Logged in with Google via Supabase');
          print('Access Token: ${accessToken.substring(0, 50)}...');
          return accessToken;
        }
      }
      
      return null;
    } catch (e) {
      print('❌ Google sign-in error: $e');
      return null;
    }
  }
  
  /// Sign in with GitHub using Supabase
  Future<String?> signInWithGitHub(BuildContext context) async {
    try {
      final response = await supabase.auth.signInWithOAuth(
        Provider.github,
        redirectTo: 'your-app://callback',
      );
      
      if (response) {
        final session = supabase.auth.currentSession;
        if (session != null) {
          return session.accessToken;
        }
      }
      
      return null;
    } catch (e) {
      print('❌ GitHub sign-in error: $e');
      return null;
    }
  }
  
  /// Use the Supabase token with API protected endpoints
  Future<Map<String, dynamic>> generateLayoutWithSupabase({
    required String accessToken,
    required double roomWidth,
    required double roomDepth,
    required List<String> objects,
  }) async {
    final response = await http.post(
      Uri.parse('$apiBaseUrl/api/protected/generate'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $accessToken',
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
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to generate layout: ${response.body}');
    }
  }
}

// ============================================================================
// FIREBASE OAUTH EXAMPLE
// ============================================================================

class FirebaseOAuthExample {
  final String apiBaseUrl;
  final firebase_auth.FirebaseAuth _firebaseAuth;
  final GoogleSignIn _googleSignIn;
  
  FirebaseOAuthExample({
    required this.apiBaseUrl,
  })  : _firebaseAuth = firebase_auth.FirebaseAuth.instance,
        _googleSignIn = GoogleSignIn();
  
  /// Sign in with Google using Firebase
  Future<String?> signInWithGoogle() async {
    try {
      // Trigger the Google Sign-In flow
      final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
      
      if (googleUser == null) {
        print('❌ Google sign-in cancelled');
        return null;
      }
      
      // Obtain the auth details from the request
      final GoogleSignInAuthentication googleAuth = await googleUser.authentication;
      
      // Create a new credential
      final credential = firebase_auth.GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );
      
      // Sign in to Firebase with the Google credential
      final userCredential = await _firebaseAuth.signInWithCredential(credential);
      
      // Get Firebase ID token
      final idToken = await userCredential.user?.getIdToken();
      
      if (idToken == null) {
        print('❌ Failed to get Firebase ID token');
        return null;
      }
      
      print('✅ Logged in with Google via Firebase');
      
      // Exchange Firebase token for API token
      final apiToken = await _verifyFirebaseToken(idToken);
      return apiToken;
      
    } catch (e) {
      print('❌ Google sign-in error: $e');
      return null;
    }
  }
  
  /// Verify Firebase token with API and get API access token
  Future<String?> _verifyFirebaseToken(String idToken) async {
    try {
      final response = await http.post(
        Uri.parse('$apiBaseUrl/auth/firebase/verify-token'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'idToken': idToken}),
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        print('✅ Firebase token verified');
        print('User ID: ${data['user_id']}');
        print('Email: ${data['email']}');
        return data['access_token'];
      } else {
        print('❌ Token verification failed: ${response.body}');
        return null;
      }
    } catch (e) {
      print('❌ Token verification error: $e');
      return null;
    }
  }
  
  /// Use the API token with protected endpoints
  Future<Map<String, dynamic>> generateLayoutWithFirebase({
    required String accessToken,
    required double roomWidth,
    required double roomDepth,
    required List<String> objects,
  }) async {
    final response = await http.post(
      Uri.parse('$apiBaseUrl/api/protected/generate'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $accessToken',
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
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to generate layout: ${response.body}');
    }
  }
  
  /// Sign out
  Future<void> signOut() async {
    await _firebaseAuth.signOut();
    await _googleSignIn.signOut();
  }
}

// ============================================================================
// FLUTTER UI EXAMPLE
// ============================================================================

class OAuthLoginScreen extends StatefulWidget {
  const OAuthLoginScreen({Key? key}) : super(key: key);

  @override
  _OAuthLoginScreenState createState() => _OAuthLoginScreenState();
}

class _OAuthLoginScreenState extends State<OAuthLoginScreen> {
  final FirebaseOAuthExample _firebaseOAuth = FirebaseOAuthExample(
    apiBaseUrl: 'http://127.0.0.1:8000',
  );
  
  bool _isLoading = false;
  String? _accessToken;
  String? _userEmail;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('OAuth Login'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Bathroom Layout Generator',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            const Text(
              'Sign in to save and manage your layouts',
              style: TextStyle(fontSize: 16, color: Colors.grey),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 48),
            
            // Google Sign-In Button
            ElevatedButton.icon(
              onPressed: _isLoading ? null : _handleGoogleSignIn,
              icon: const Icon(Icons.login),
              label: const Text('Sign in with Google'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
                backgroundColor: Colors.white,
                foregroundColor: Colors.black87,
              ),
            ),
            
            const SizedBox(height: 16),
            
            // GitHub Sign-In Button (Supabase)
            ElevatedButton.icon(
              onPressed: _isLoading ? null : _handleGitHubSignIn,
              icon: const Icon(Icons.code),
              label: const Text('Sign in with GitHub'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
                backgroundColor: Colors.black87,
                foregroundColor: Colors.white,
              ),
            ),
            
            const SizedBox(height: 32),
            
            if (_isLoading)
              const Center(child: CircularProgressIndicator()),
            
            if (_accessToken != null) ...[
              const Divider(),
              const SizedBox(height: 16),
              Text(
                '✅ Logged in successfully!',
                style: const TextStyle(
                  color: Colors.green,
                  fontWeight: FontWeight.bold,
                ),
                textAlign: TextAlign.center,
              ),
              if (_userEmail != null)
                Text(
                  'Email: $_userEmail',
                  textAlign: TextAlign.center,
                ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _navigateToHome,
                child: const Text('Continue to App'),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Future<void> _handleGoogleSignIn() async {
    setState(() => _isLoading = true);
    
    try {
      final token = await _firebaseOAuth.signInWithGoogle();
      
      if (token != null) {
        setState(() {
          _accessToken = token;
          _isLoading = false;
        });
        
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Signed in with Google!')),
        );
      } else {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Sign-in cancelled or failed')),
        );
      }
    } catch (e) {
      setState(() => _isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    }
  }

  Future<void> _handleGitHubSignIn() async {
    // This would use Supabase OAuth
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('GitHub sign-in requires Supabase configuration'),
      ),
    );
  }

  void _navigateToHome() {
    // Navigate to home screen with the access token
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (context) => HomeScreen(accessToken: _accessToken!),
      ),
    );
  }
}

class HomeScreen extends StatelessWidget {
  final String accessToken;

  const HomeScreen({Key? key, required this.accessToken}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Bathroom Layout Generator'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              final firebaseOAuth = FirebaseOAuthExample(
                apiBaseUrl: 'http://127.0.0.1:8000',
              );
              await firebaseOAuth.signOut();
              Navigator.pushReplacement(
                context,
                MaterialPageRoute(
                  builder: (context) => const OAuthLoginScreen(),
                ),
              );
            },
          ),
        ],
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text(
              'You are logged in!',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            Text('Access Token: ${accessToken.substring(0, 20)}...'),
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: () {
                // Generate a layout
              },
              child: const Text('Generate Bathroom Layout'),
            ),
          ],
        ),
      ),
    );
  }
}

// ============================================================================
// MAIN APP
// ============================================================================

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Supabase (if using)
  // await Supabase.initialize(
  //   url: 'YOUR_SUPABASE_URL',
  //   anonKey: 'YOUR_SUPABASE_ANON_KEY',
  // );
  
  // Initialize Firebase (if using)
  // await Firebase.initializeApp();
  
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Bathroom Layout Generator',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: const OAuthLoginScreen(),
    );
  }
}
