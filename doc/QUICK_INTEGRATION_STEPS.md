# Quick Integration Steps - Flutter Phone App

## 🚀 5-Minute Setup

### Step 1: Add Service File (1 min)

Copy `bathroom_api_auth_service.dart` to your project:
```
lib/services/bathroom_api_auth_service.dart
```

Update the IP address on line 13:
```dart
static const String baseUrl = 'http://YOUR_COMPUTER_IP:8000';
```

### Step 2: Update Login Screen (2 min)

In `welcome_back_screen.dart`, add these 3 changes:

**Change 1 - Add import:**
```dart
import 'package:vid_app/services/bathroom_api_auth_service.dart';
```

**Change 2 - Add service instance:**
```dart
class WelcomeBackScreenState extends ConsumerState<WelcomeBackScreen> {
  final AwsAuth _awsAuth = AwsAuth();
  final BathroomApiAuthService _bathroomApi = BathroomApiAuthService(); // ADD THIS
  
  @override
  void initState() {
    super.initState();
    _bathroomApi.init(); // ADD THIS
  }
```

**Change 3 - Update login button:**
```dart
onPressed: () async {
  if (_formKey.currentState!.validate()) {
    // Existing AWS login
    await _awsAuth.signInUser(
      email: welcomeBackState.emailController.text,
      password: welcomeBackState.passwordController.text,
    );
    
    // ADD THIS: Sync with bathroom API
    await _bathroomApi.syncWithAwsLogin(
      email: welcomeBackState.emailController.text,
      password: welcomeBackState.passwordController.text,
    );
    
    // Navigate to home...
  }
}
```

### Step 3: Start API Server (1 min)

```bash
cd c:\Users\User\flutter_projects_myvid\streamlit_app
python api.py
```

### Step 4: Find Your Computer's IP (1 min)

```bash
ipconfig
```

Look for IPv4 Address (e.g., `192.168.1.100`)

Update in `bathroom_api_auth_service.dart`:
```dart
static const String baseUrl = 'http://192.168.1.100:8000';
```

### Step 5: Test (1 min)

1. Connect phone to same WiFi as computer
2. Run your Flutter app
3. Login with credentials
4. Check console for: ✅ Bathroom API sync successful

## ✅ Done!

Your app now has bathroom layout generation capabilities!

## 📱 Using Layouts in Your App

```dart
final bathroomApi = BathroomApiAuthService();

// Generate layout
final layout = await bathroomApi.generateLayout(
  roomWidth: 300,
  roomDepth: 240,
  roomHeight: 280,
  objectsToPlace: ['toilet', 'sink', 'shower'],
);

print('Layout ID: ${layout!['layout_id']}');
print('Score: ${layout['score']}');
```

## 🔧 Troubleshooting

**Can't connect to API?**
- Check phone and computer on same WiFi
- Verify IP address is correct
- Try accessing `http://YOUR_IP:8000` in phone browser

**Login fails?**
- Check API is running: `python api.py`
- Check Supabase is configured (see FLUTTER_PHONE_SETUP.md)

## 📚 Full Documentation

- `FLUTTER_PHONE_SETUP.md` - Complete setup guide
- `bathroom_api_auth_service.dart` - Service implementation
- `welcome_back_screen_integrated.dart` - Full example

## 🎯 What You Get

- ✅ Automatic bathroom layout generation
- ✅ User-specific layout storage
- ✅ Layout history and management
- ✅ Works alongside AWS Cognito
- ✅ Non-blocking (app works even if API is down)
