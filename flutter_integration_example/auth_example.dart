import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:firebase_auth/firebase_auth.dart' as firebase;
import 'package:supabase_flutter/supabase_flutter.dart';

// API client for authentication
class AuthApiClient {
  final String baseUrl;
  String? _accessToken;
  
  AuthApiClient({required this.baseUrl});
  
  // Set token after login
  set accessToken(String? token) {
    _accessToken = token;
  }
  
  // Get the current token
  String? get accessToken => _accessToken;
  
  // Check if user is logged in
  bool get isLoggedIn => _accessToken != null;
  
  // Headers for authenticated requests
  Map<String, String> get authHeaders => {
    'Content-Type': 'application/json',
    if (_accessToken != null) 'Authorization': 'Bearer $_accessToken',
  };
  
  // Login with email and password
  Future<Map<String, dynamic>> login(String email, String password) async {
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
      return data;
    } else {
      throw Exception('Failed to login: ${response.body}');
    }
  }
  
  // Register new user
  Future<Map<String, dynamic>> register(String email, String password, String fullName) async {
    final response = await http.post(
      Uri.parse('$baseUrl/users/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'password': password,
        'full_name': fullName,
      }),
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to register: ${response.body}');
    }
  }
  
  // Get current user profile
  Future<Map<String, dynamic>> getUserProfile() async {
    if (_accessToken == null) {
      throw Exception('Not authenticated');
    }
    
    final response = await http.get(
      Uri.parse('$baseUrl/users/me/'),
      headers: authHeaders,
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to get user profile: ${response.body}');
    }
  }
  
  // Logout
  Future<void> logout() async {
    if (_accessToken == null) {
      return;
    }
    
    try {
      await http.post(
        Uri.parse('$baseUrl/logout'),
        headers: authHeaders,
      );
    } catch (e) {
      print('Error during logout: $e');
    } finally {
      _accessToken = null;
    }
  }
  
  // Verify Firebase token
  Future<Map<String, dynamic>> verifyFirebaseToken(String idToken) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/firebase/verify-token'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'idToken': idToken}),
    );
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      _accessToken = data['access_token'];
      return data;
    } else {
      throw Exception('Failed to verify token: ${response.body}');
    }
  }
}

// Auth service to manage authentication state
class AuthService {
  static final AuthService _instance = AuthService._internal();
  factory AuthService() => _instance;
  
  AuthService._internal();
  
  late final AuthApiClient _apiClient;
  firebase.FirebaseAuth? _firebaseAuth;
  GotrueClient? _supabaseAuth;
  
  // Initialize the auth service
  Future<void> init(String baseUrl) async {
    _apiClient = AuthApiClient(baseUrl: baseUrl);
    
    // Load saved token from shared preferences
    final prefs = await SharedPreferences.getInstance();
    final savedToken = prefs.getString('auth_token');
    if (savedToken != null) {
      _apiClient.accessToken = savedToken;
    }
  }
  
  // Initialize Firebase auth
  void initFirebase(firebase.FirebaseAuth auth) {
    _firebaseAuth = auth;
  }
  
  // Initialize Supabase auth
  void initSupabase(GotrueClient auth) {
    _supabaseAuth = auth;
  }
  
  // Login with email and password
  Future<bool> login(String email, String password) async {
    try {
      final authResult = await _apiClient.login(email, password);
      
      // Save token to shared preferences
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('auth_token', authResult['access_token']);
      
      return true;
    } catch (e) {
      print('Login error: $e');
      return false;
    }
  }
  
  // Login with Firebase
  Future<bool> loginWithFirebase() async {
    try {
      if (_firebaseAuth == null) {
        throw Exception('Firebase auth not initialized');
      }
      
      // Sign in with Google through Firebase
      final googleProvider = firebase.GoogleAuthProvider();
      final userCredential = await _firebaseAuth!.signInWithPopup(googleProvider);
      
      // Get Firebase ID token
      final idToken = await userCredential.user?.getIdToken();
      if (idToken == null) {
        throw Exception('Failed to get ID token');
      }
      
      // Verify token with our backend
      final tokenResult = await _apiClient.verifyFirebaseToken(idToken);
      
      // Save token to shared preferences
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('auth_token', tokenResult['access_token']);
      
      return true;
    } catch (e) {
      print('Firebase login error: $e');
      return false;
    }
  }
  
  // Login with Supabase
  Future<bool> loginWithSupabase(String email, String password) async {
    try {
      if (_supabaseAuth == null) {
        throw Exception('Supabase auth not initialized');
      }
      
      final response = await _supabaseAuth!.signIn(
        email: email,
        password: password,
      );
      
      if (response.error != null) {
        throw Exception(response.error!.message);
      }
      
      final session = response.data!;
      
      // Use the Supabase token directly with our API
      _apiClient.accessToken = session.accessToken;
      
      // Save token to shared preferences
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('auth_token', session.accessToken);
      
      return true;
    } catch (e) {
      print('Supabase login error: $e');
      return false;
    }
  }
  
  // Register new user
  Future<bool> register(String email, String password, String fullName) async {
    try {
      await _apiClient.register(email, password, fullName);
      return true;
    } catch (e) {
      print('Registration error: $e');
      return false;
    }
  }
  
  // Logout
  Future<void> logout() async {
    try {
      await _apiClient.logout();
      
      // Also sign out from Firebase and Supabase if applicable
      _firebaseAuth?.signOut();
      _supabaseAuth?.signOut();
      
      // Clear saved token
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove('auth_token');
    } catch (e) {
      print('Logout error: $e');
    }
  }
  
  // Get current auth status
  bool get isLoggedIn => _apiClient.isLoggedIn;
  
  // Get auth client for API requests
  AuthApiClient get apiClient => _apiClient;
}

// Example login screen widget
class LoginScreen extends StatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _auth = AuthService();
  bool _isLoading = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Bathroom Layout Generator')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text(
              'Login',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 32),
            TextField(
              controller: _emailController,
              decoration: const InputDecoration(
                labelText: 'Email',
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.emailAddress,
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _passwordController,
              decoration: const InputDecoration(
                labelText: 'Password',
                border: OutlineInputBorder(),
              ),
              obscureText: true,
            ),
            const SizedBox(height: 32),
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _handleLogin,
                child: _isLoading
                    ? const CircularProgressIndicator()
                    : const Text('Login'),
              ),
            ),
            const SizedBox(height: 16),
            TextButton(
              onPressed: () {
                // Navigate to registration screen
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => RegisterScreen()),
                );
              },
              child: const Text('Create Account'),
            ),
            const Divider(height: 40),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                ElevatedButton.icon(
                  onPressed: _handleGoogleLogin,
                  icon: const Icon(Icons.login),
                  label: const Text('Google'),
                ),
                ElevatedButton.icon(
                  onPressed: _handleGithubLogin,
                  icon: const Icon(Icons.code),
                  label: const Text('GitHub'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _handleLogin() async {
    setState(() => _isLoading = true);
    
    try {
      final success = await _auth.login(
        _emailController.text.trim(),
        _passwordController.text,
      );
      
      if (success && mounted) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (context) => HomeScreen()),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Login failed')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _handleGoogleLogin() async {
    setState(() => _isLoading = true);
    
    try {
      final success = await _auth.loginWithFirebase();
      
      if (success && mounted) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (context) => HomeScreen()),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Google login failed')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _handleGithubLogin() async {
    // GitHub login implementation
  }
}

// Example registration screen
class RegisterScreen extends StatefulWidget {
  const RegisterScreen({Key? key}) : super(key: key);

  @override
  _RegisterScreenState createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _nameController = TextEditingController();
  final _auth = AuthService();
  bool _isLoading = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Create Account')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TextField(
              controller: _nameController,
              decoration: const InputDecoration(
                labelText: 'Full Name',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _emailController,
              decoration: const InputDecoration(
                labelText: 'Email',
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.emailAddress,
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _passwordController,
              decoration: const InputDecoration(
                labelText: 'Password',
                border: OutlineInputBorder(),
              ),
              obscureText: true,
            ),
            const SizedBox(height: 32),
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _handleRegister,
                child: _isLoading
                    ? const CircularProgressIndicator()
                    : const Text('Create Account'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _handleRegister() async {
    setState(() => _isLoading = true);
    
    try {
      final success = await _auth.register(
        _emailController.text.trim(),
        _passwordController.text,
        _nameController.text.trim(),
      );
      
      if (success && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Account created successfully')),
        );
        Navigator.pop(context); // Go back to login screen
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Registration failed')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }
}

// Home screen (after login)
class HomeScreen extends StatelessWidget {
  final _auth = AuthService();

  HomeScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Bathroom Layout Generator'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await _auth.logout();
              Navigator.pushReplacement(
                context,
                MaterialPageRoute(builder: (context) => LoginScreen()),
              );
            },
          ),
        ],
      ),
      body: const Center(
        child: Text('You are logged in! Bathroom layout features here.'),
      ),
    );
  }
}

// Main app entry point
class AuthExampleApp extends StatelessWidget {
  const AuthExampleApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Bathroom Layout Generator',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: FutureBuilder<void>(
        future: _initializeAuth(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Scaffold(
              body: Center(child: CircularProgressIndicator()),
            );
          }
          
          final authService = AuthService();
          return authService.isLoggedIn ? HomeScreen() : LoginScreen();
        },
      ),
    );
  }

  Future<void> _initializeAuth() async {
    // Initialize AuthService with API base URL
    await AuthService().init('http://your-api-url.com');
  }
}
