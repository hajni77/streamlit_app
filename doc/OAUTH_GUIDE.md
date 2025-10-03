# OAuth Authentication Guide

Complete guide for implementing OAuth authentication with the Bathroom Layout Generator API.

## Why OAuth?

✅ **No email confirmation needed** - Users can login immediately
✅ **Better security** - Leverages trusted providers (Google, GitHub)
✅ **Better UX** - One-click login, no password to remember
✅ **Industry standard** - Used by most modern applications

## Overview

```
User clicks "Sign in with Google"
    ↓
Redirected to Google login
    ↓
User authorizes app
    ↓
Google redirects back with token
    ↓
Exchange token for API access token
    ↓
Use API token for protected endpoints
```

## Option 1: Supabase OAuth (Recommended)

### Setup Steps

#### 1. Configure Supabase

1. Go to: https://app.supabase.com
2. Select your project
3. Navigate to: **Authentication** → **Providers**
4. Enable your desired provider(s):

**For Google:**
- Toggle **Google** to enabled
- Add your Google OAuth credentials:
  - Client ID: Get from Google Cloud Console
  - Client Secret: Get from Google Cloud Console
- Save

**For GitHub:**
- Toggle **GitHub** to enabled
- Add GitHub OAuth credentials:
  - Client ID: Get from GitHub Developer Settings
  - Client Secret: Get from GitHub Developer Settings
- Save

#### 2. Configure Redirect URLs

Add these redirect URLs in Supabase:
- Development: `http://localhost:8080/callback`
- Production: `https://your-domain.com/callback`
- Flutter: `your-app://callback`

#### 3. Update .env File

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SECRET_KEY=your_random_secret_key
```

### Implementation

#### Flutter/Dart

```dart
import 'package:supabase_flutter/supabase_flutter.dart';

// Initialize Supabase
await Supabase.initialize(
  url: 'YOUR_SUPABASE_URL',
  anonKey: 'YOUR_SUPABASE_ANON_KEY',
);

final supabase = Supabase.instance.client;

// Sign in with Google
Future<void> signInWithGoogle() async {
  final response = await supabase.auth.signInWithOAuth(
    Provider.google,
    redirectTo: 'your-app://callback',
  );
  
  if (response) {
    // Get the session
    final session = supabase.auth.currentSession;
    final accessToken = session?.accessToken;
    
    // Use this token with your API
    print('Access Token: $accessToken');
  }
}

// Sign in with GitHub
Future<void> signInWithGitHub() async {
  await supabase.auth.signInWithOAuth(
    Provider.github,
    redirectTo: 'your-app://callback',
  );
}

// Use token with API
Future<void> generateLayout(String token) async {
  final response = await http.post(
    Uri.parse('http://127.0.0.1:8000/api/protected/generate'),
    headers: {
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
    },
    body: jsonEncode({
      'id': 'layout_1',
      'room_width': 300,
      'room_depth': 240,
      'room_height': 280,
      'objects_to_place': ['toilet', 'sink', 'shower'],
      'windows_doors': [],
      'beam_width': 10,
    }),
  );
  
  if (response.statusCode == 200) {
    final layout = jsonDecode(response.body);
    print('Layout generated: ${layout['layout_id']}');
  }
}
```

#### Web/JavaScript

```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  'YOUR_SUPABASE_URL',
  'YOUR_SUPABASE_ANON_KEY'
)

// Sign in with Google
async function signInWithGoogle() {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: 'http://localhost:3000/callback'
    }
  })
}

// Get session
const { data: { session } } = await supabase.auth.getSession()
const accessToken = session?.access_token

// Use with API
fetch('http://127.0.0.1:8000/api/protected/generate', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    id: 'layout_1',
    room_width: 300,
    room_depth: 240,
    room_height: 280,
    objects_to_place: ['toilet', 'sink', 'shower'],
    windows_doors: [],
    beam_width: 10,
  })
})
```

## Option 2: Firebase OAuth

### Setup Steps

#### 1. Configure Firebase

1. Go to: https://console.firebase.google.com
2. Select your project
3. Navigate to: **Authentication** → **Sign-in method**
4. Enable providers:

**For Google:**
- Click **Google**
- Toggle to **Enable**
- Add support email
- Save

**For GitHub:**
- Click **GitHub**
- Toggle to **Enable**
- Add Client ID and Secret from GitHub
- Save

#### 2. Update .env File

```env
# Place firebase_credentials.json in project root
SECRET_KEY=your_random_secret_key
```

### Implementation

#### Flutter/Dart

```dart
import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';

final FirebaseAuth _auth = FirebaseAuth.instance;
final GoogleSignIn _googleSignIn = GoogleSignIn();

// Sign in with Google
Future<String?> signInWithGoogle() async {
  // Trigger Google Sign-In
  final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
  
  if (googleUser == null) return null;
  
  // Get auth details
  final GoogleSignInAuthentication googleAuth = 
      await googleUser.authentication;
  
  // Create credential
  final credential = GoogleAuthProvider.credential(
    accessToken: googleAuth.accessToken,
    idToken: googleAuth.idToken,
  );
  
  // Sign in to Firebase
  final userCredential = await _auth.signInWithCredential(credential);
  
  // Get Firebase ID token
  final idToken = await userCredential.user?.getIdToken();
  
  // Exchange for API token
  final apiToken = await verifyFirebaseToken(idToken!);
  return apiToken;
}

// Verify Firebase token with API
Future<String?> verifyFirebaseToken(String idToken) async {
  final response = await http.post(
    Uri.parse('http://127.0.0.1:8000/auth/firebase/verify-token'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({'idToken': idToken}),
  );
  
  if (response.statusCode == 200) {
    final data = jsonDecode(response.body);
    return data['access_token'];
  }
  return null;
}

// Use with API
Future<void> generateLayout(String token) async {
  final response = await http.post(
    Uri.parse('http://127.0.0.1:8000/api/protected/generate'),
    headers: {
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
    },
    body: jsonEncode({
      'id': 'layout_1',
      'room_width': 300,
      'room_depth': 240,
      'room_height': 280,
      'objects_to_place': ['toilet', 'sink', 'shower'],
      'windows_doors': [],
      'beam_width': 10,
    }),
  );
}
```

## Getting OAuth Credentials

### Google OAuth

1. Go to: https://console.cloud.google.com
2. Create a new project (or select existing)
3. Navigate to: **APIs & Services** → **Credentials**
4. Click: **Create Credentials** → **OAuth 2.0 Client ID**
5. Configure consent screen if needed
6. Choose application type:
   - **Web application** for web apps
   - **Android** for Android apps
   - **iOS** for iOS apps
7. Add authorized redirect URIs:
   - `http://localhost:8080/callback` (development)
   - Your production callback URL
8. Copy **Client ID** and **Client Secret**

### GitHub OAuth

1. Go to: https://github.com/settings/developers
2. Click: **New OAuth App**
3. Fill in:
   - Application name: Your app name
   - Homepage URL: Your app URL
   - Authorization callback URL: `http://localhost:8080/callback`
4. Click: **Register application**
5. Copy **Client ID**
6. Generate and copy **Client Secret**

## Testing OAuth

### Test with Python Script

```bash
python oauth_example.py
```

Choose option 1 (Supabase) or 2 (Firebase) to see detailed setup instructions.

### Test with Flutter

See complete example in:
```
flutter_integration_example/oauth_flutter_example.dart
```

## Common Issues

### "OAuth provider not configured"

**Solution**: Enable the provider in Supabase/Firebase dashboard

### "Redirect URI mismatch"

**Solution**: Ensure redirect URI in code matches the one configured in provider settings

### "Invalid client"

**Solution**: Check that Client ID and Secret are correct

### "Token verification failed"

**Solution**: 
- Ensure API is running
- Check `.env` configuration
- Verify Firebase credentials are valid

## Security Best Practices

1. **Never expose secrets** - Keep Client Secrets secure
2. **Use HTTPS in production** - Always use secure connections
3. **Validate tokens** - API validates all tokens before use
4. **Short token expiry** - Tokens expire after 30 minutes (configurable)
5. **Secure storage** - Store tokens securely on client
6. **Logout properly** - Clear tokens on logout

## Production Checklist

- [ ] OAuth providers configured in Supabase/Firebase
- [ ] Production redirect URLs added
- [ ] Client ID and Secret secured
- [ ] HTTPS enabled
- [ ] Token refresh implemented (if needed)
- [ ] Error handling implemented
- [ ] Logout functionality working
- [ ] Token storage secured

## Next Steps

1. Choose OAuth provider (Supabase or Firebase)
2. Configure provider in dashboard
3. Get OAuth credentials (Google, GitHub, etc.)
4. Implement in your Flutter/Web app
5. Test the flow
6. Deploy to production

## Resources

- **Supabase Auth Docs**: https://supabase.com/docs/guides/auth
- **Firebase Auth Docs**: https://firebase.google.com/docs/auth
- **Google OAuth**: https://developers.google.com/identity/protocols/oauth2
- **GitHub OAuth**: https://docs.github.com/en/developers/apps/building-oauth-apps

## Example Files

- `oauth_example.py` - Python OAuth examples and guides
- `flutter_integration_example/oauth_flutter_example.dart` - Complete Flutter implementation
- `FIX_LOGIN_ISSUE.md` - Fix current email confirmation issue
