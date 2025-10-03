# Fix Login Issue - Email Confirmation Required

## Current Problem

✅ **Registration succeeded**: User `frecskahajni@gmail.com` was created
❌ **Login failed**: "Invalid login credentials" error

**Root Cause**: Supabase requires email confirmation by default before users can log in.

## Quick Solutions

### Solution 1: Disable Email Confirmation (Development Only)

**⚠️ For development/testing only - NOT for production!**

1. Go to your Supabase Dashboard: https://app.supabase.com
2. Select your project
3. Navigate to: **Authentication** → **Settings**
4. Find: **"Enable email confirmations"**
5. **Disable** this setting
6. Try logging in again:
   ```bash
   python register_user_example.py
   # Use the same credentials
   ```

### Solution 2: Confirm Email Manually in Dashboard

1. Go to Supabase Dashboard
2. Navigate to: **Authentication** → **Users**
3. Find user: `frecskahajni@gmail.com`
4. Click on the user
5. Click **"Confirm email"** button
6. Try logging in again

### Solution 3: Check Your Email

1. Check inbox for: `frecskahajni@gmail.com`
2. Look for email from Supabase
3. Click the confirmation link
4. Return to app and login

### Solution 4: Use OAuth Instead (Recommended)

OAuth providers (Google, GitHub) bypass email confirmation:

```bash
python oauth_example.py
```

Choose option 1 or 2 to see setup instructions.

## Testing the Fix

After applying any solution above, test login:

```bash
python register_user_example.py
```

Enter the same credentials:
- Email: `frecskahajni@gmail.com`
- Password: `hajni2001`

Expected result:
```
✅ Login successful!
   Token Type: bearer
   Provider: supabase
   Access Token: eyJ0eXAi...
```

## OAuth Setup (Better Long-term Solution)

### For Supabase + Google OAuth:

1. **Configure Supabase:**
   - Go to: Authentication → Providers
   - Enable **Google** provider
   - Add your Google OAuth credentials
   - Set redirect URL: `http://localhost:8080/callback`

2. **In Flutter app:**
   ```dart
   final response = await supabase.auth.signInWithOAuth(
     Provider.google,
     redirectTo: 'your-app://callback',
   );
   ```

3. **Benefits:**
   - No email confirmation needed
   - Better user experience
   - More secure
   - Faster login

### For Firebase + Google OAuth:

1. **Configure Firebase:**
   - Go to Firebase Console
   - Authentication → Sign-in method
   - Enable **Google** provider

2. **In Flutter app:**
   See `flutter_integration_example/oauth_flutter_example.dart`

3. **Exchange token:**
   ```bash
   curl -X POST http://127.0.0.1:8000/auth/firebase/verify-token \
     -H "Content-Type: application/json" \
     -d '{"idToken":"YOUR_FIREBASE_TOKEN"}'
   ```

## Files to Help You

- **`oauth_example.py`** - OAuth setup guide and examples
- **`flutter_integration_example/oauth_flutter_example.dart`** - Complete Flutter OAuth implementation
- **`HOW_TO_REGISTER.md`** - General registration guide
- **`REGISTRATION_SUMMARY.md`** - Quick reference

## Recommended Approach for Production

1. **Use OAuth** (Google, GitHub, etc.)
   - Best user experience
   - No email confirmation issues
   - Industry standard

2. **If using email/password:**
   - Keep email confirmation enabled
   - Implement proper email verification flow
   - Add "Resend confirmation email" feature
   - Show clear messages to users

3. **Hybrid approach:**
   - Offer both OAuth and email/password
   - Let users choose their preferred method

## Next Steps

1. Choose a solution above
2. Test login with your credentials
3. Once working, generate a layout:
   ```bash
   curl -X POST http://127.0.0.1:8000/api/protected/generate \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "id": "test_layout",
       "room_width": 300,
       "room_depth": 240,
       "room_height": 280,
       "objects_to_place": ["toilet", "sink", "shower"],
       "windows_doors": [],
       "beam_width": 10
     }'
   ```

## Support

If issues persist:
1. Check Supabase logs in dashboard
2. Verify `.env` configuration
3. Ensure API is running: `python api.py`
4. Check API logs for error messages
