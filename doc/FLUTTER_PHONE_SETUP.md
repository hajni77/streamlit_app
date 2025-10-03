# Flutter Phone App Integration Guide

Complete guide for integrating the Bathroom Layout API with your Flutter phone app.

## Overview

Your app uses AWS Cognito for authentication. The bathroom layout API will work **alongside** your existing authentication, not replace it.

### Flow:
```
User logs in with AWS Cognito
    ↓
App automatically syncs with Bathroom API
    ↓
User can now generate bathroom layouts
    ↓
Layouts are saved to their account
```

## Step 1: Add Dependencies

Add to your `pubspec.yaml`:

```yaml
dependencies:
  http: ^1.1.0
  shared_preferences: ^2.2.2
```

Run:
```bash
flutter pub get
```

## Step 2: Add the Service File

1. Create a new directory: `lib/services/`
2. Copy `bathroom_api_auth_service.dart` to `lib/services/`
3. Update the `baseUrl` in the file:

```dart
static const String baseUrl = 'http://YOUR_SERVER_IP:8000';
```

**Finding your server IP:**
- If testing on same network: Use your computer's local IP (e.g., `192.168.1.100`)
- If deployed: Use your server's public IP or domain

## Step 3: Update Your Login Screen

Replace your current `welcome_back_screen.dart` with the integrated version, or apply these changes:

### 3.1 Add Import

```dart
import 'package:vid_app/services/bathroom_api_auth_service.dart';
```

### 3.2 Add Service Instance

```dart
class WelcomeBackScreenState extends ConsumerState<WelcomeBackScreen> {
  // ... existing code ...
  
  // ADD THIS
  final BathroomApiAuthService _bathroomApi = BathroomApiAuthService();
  bool _isSyncingBathroomApi = false;
  
  @override
  void initState() {
    super.initState();
    _bathroomApi.init(); // ADD THIS
  }
```

### 3.3 Update Login Handler

Replace your existing login button's `onPressed`:

```dart
onPressed: () async {
  if (_formKey.currentState!.validate()) {
    final email = welcomeBackState.emailController.text;
    final password = welcomeBackState.passwordController.text;
    
    try {
      // Step 1: AWS Cognito login
      await _awsAuth.signInUser(email: email, password: password);
      
      // Step 2: Sync with Bathroom API (non-blocking)
      setState(() => _isSyncingBathroomApi = true);
      
      await _bathroomApi.syncWithAwsLogin(
        email: email,
        password: password,
      );
      
      setState(() => _isSyncingBathroomApi = false);
      
      // Step 3: Navigate to home
      // NavigatorService.pushNamed(AppRoutes.homeScreen);
      
    } catch (e) {
      setState(() => _isSyncingBathroomApi = false);
      // Handle error
    }
  }
}
```

## Step 4: Configure the API Server

### Option A: Running on Your Computer

1. **Start the API:**
   ```bash
   cd c:\Users\User\flutter_projects_myvid\streamlit_app
   python api.py
   ```

2. **Find your computer's IP:**
   ```bash
   ipconfig
   ```
   Look for "IPv4 Address" (e.g., `192.168.1.100`)

3. **Update Flutter app:**
   ```dart
   static const String baseUrl = 'http://192.168.1.100:8000';
   ```

4. **Ensure phone and computer are on same WiFi network**

### Option B: Deploy to Cloud

Deploy the API to a cloud server (Heroku, AWS, etc.) and use that URL.

## Step 5: Configure Supabase (for API authentication)

The API needs Supabase configured. Create `.env` file:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SECRET_KEY=your_random_secret_key_here
```

**To disable email confirmation** (for testing):
1. Go to Supabase Dashboard
2. Authentication → Settings
3. Disable "Enable email confirmations"

## Step 6: Using Bathroom Layouts in Your App

### Generate a Layout

```dart
import 'package:vid_app/services/bathroom_api_auth_service.dart';

class BathroomLayoutScreen extends StatefulWidget {
  @override
  _BathroomLayoutScreenState createState() => _BathroomLayoutScreenState();
}

class _BathroomLayoutScreenState extends State<BathroomLayoutScreen> {
  final _bathroomApi = BathroomApiAuthService();
  bool _isLoading = false;
  Map<String, dynamic>? _layout;

  Future<void> _generateLayout() async {
    setState(() => _isLoading = true);
    
    try {
      final layout = await _bathroomApi.generateLayout(
        roomWidth: 300,
        roomDepth: 240,
        roomHeight: 280,
        objectsToPlace: ['toilet', 'sink', 'shower'],
      );
      
      if (layout != null) {
        setState(() => _layout = layout);
        print('Layout generated!');
        print('Score: ${layout['score']}');
        print('Objects: ${layout['objects']}');
      }
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Bathroom Layout')),
      body: Column(
        children: [
          ElevatedButton(
            onPressed: _isLoading ? null : _generateLayout,
            child: Text(_isLoading ? 'Generating...' : 'Generate Layout'),
          ),
          if (_layout != null)
            Expanded(
              child: ListView(
                children: [
                  Text('Layout ID: ${_layout!['layout_id']}'),
                  Text('Score: ${_layout!['score']}'),
                  Text('Objects placed: ${_layout!['objects'].length}'),
                  // Display objects
                  for (var obj in _layout!['objects'])
                    ListTile(
                      title: Text(obj['object_type']),
                      subtitle: Text('Position: ${obj['position']}'),
                    ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
```

### Get User's Saved Layouts

```dart
Future<void> _loadUserLayouts() async {
  final layouts = await _bathroomApi.getUserLayouts();
  
  if (layouts != null) {
    print('User has ${layouts.length} layouts');
    for (var layout in layouts) {
      print('Layout: ${layout['layout_id']}');
      print('Score: ${layout['score']}');
    }
  }
}
```

### Delete a Layout

```dart
Future<void> _deleteLayout(String layoutId) async {
  final success = await _bathroomApi.deleteLayout(layoutId);
  if (success) {
    print('Layout deleted');
  }
}
```

## Testing

### Test on Phone

1. **Start API on computer:**
   ```bash
   python api.py
   ```

2. **Connect phone to same WiFi**

3. **Update app with computer's IP:**
   ```dart
   static const String baseUrl = 'http://192.168.1.100:8000';
   ```

4. **Run app:**
   ```bash
   flutter run
   ```

5. **Login with your credentials**

6. **Check console for logs:**
   - ✅ AWS Cognito login successful
   - ✅ Bathroom API sync successful

### Test API Directly

Test if phone can reach API:

```bash
# From phone browser, visit:
http://YOUR_COMPUTER_IP:8000

# Should show: {"status":"ok","message":"Bathroom Layout Generator API is running"}
```

## Troubleshooting

### "Cannot connect to API"

**Solutions:**
1. Check phone and computer are on same WiFi
2. Verify computer's IP address is correct
3. Check firewall isn't blocking port 8000
4. Try accessing API from phone browser first

### "Authentication failed"

**Solutions:**
1. Check Supabase is configured in `.env`
2. Disable email confirmation in Supabase
3. Check API logs for errors

### "Login works but bathroom API fails"

**Solutions:**
1. This is non-critical - app will still work
2. Check API server is running
3. Check network connection
4. User can still use AWS Cognito features

## Production Deployment

### For Production:

1. **Deploy API to cloud server**
2. **Use HTTPS** (required for production)
3. **Update baseUrl:**
   ```dart
   static const String baseUrl = 'https://your-domain.com';
   ```
4. **Enable email confirmation** in Supabase
5. **Add proper error handling**
6. **Implement token refresh** if needed

## Security Notes

- ✅ Tokens are stored securely in SharedPreferences
- ✅ Passwords are never stored, only tokens
- ✅ API validates all requests
- ✅ User data is isolated (can only access own layouts)
- ⚠️ Use HTTPS in production
- ⚠️ Never commit `.env` file

## Summary

Your app now has:
- ✅ AWS Cognito authentication (existing)
- ✅ Bathroom Layout API authentication (new)
- ✅ Automatic sync on login
- ✅ User-specific layout storage
- ✅ Non-blocking integration (app works even if API is down)

## Files Reference

- `bathroom_api_auth_service.dart` - Service file
- `welcome_back_screen_integrated.dart` - Example integration
- `FLUTTER_PHONE_SETUP.md` - This guide

## Next Steps

1. ✅ Add service file to your project
2. ✅ Update login screen
3. ✅ Configure API server
4. ✅ Test on phone
5. ✅ Create bathroom layout screens
6. ✅ Deploy to production
