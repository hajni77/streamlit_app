# User Registration - Summary

## What Was Fixed

The API had an import error with Supabase dependencies. I've updated `user_api.py` to handle optional dependencies gracefully:

### Changes Made:

1. **Optional Imports** - Supabase and Firebase are now optional
   - If not installed, the API will print a warning but still start
   - Authentication will work with whichever provider is available

2. **Graceful Degradation**
   - API can start without Supabase/Firebase
   - Clear error messages when auth providers aren't configured
   - Better error handling for missing dependencies

## How to Register a User

### Quick Method (Recommended):

```bash
# 1. Start the API
python api.py

# 2. In another terminal, run the registration script
python register_user_example.py

# 3. Follow the prompts
```

### Manual Method (cURL):

```bash
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123",
    "full_name": "John Doe"
  }'
```

## Configuration Required

Create a `.env` file with at least one auth provider:

### Option 1: Supabase (Recommended)
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SECRET_KEY=your_random_secret_key
```

### Option 2: Firebase
```env
# Place firebase_credentials.json in project root
SECRET_KEY=your_random_secret_key
```

## Files Created

1. **`register_user_example.py`** - Interactive registration script
2. **`HOW_TO_REGISTER.md`** - Complete registration guide
3. **`REGISTRATION_SUMMARY.md`** - This file

## Registration Flow

```
1. User provides: email, password, full_name
   ↓
2. API validates input (email format, required fields)
   ↓
3. API tries to create user:
   - First tries Supabase (if configured)
   - Falls back to Firebase (if configured)
   - Returns error if neither is available
   ↓
4. Returns user info: {id, email, full_name}
   ↓
5. User can now login to get access token
   ↓
6. Use token for protected endpoints
```

## After Registration

### Login:
```bash
curl -X POST http://localhost:8000/token \
  -d "username=user@example.com&password=securepass123"
```

### Response:
```json
{
  "access_token": "eyJ0eXAi...",
  "token_type": "bearer",
  "provider": "supabase"
}
```

### Use Token:
```bash
curl -X GET http://localhost:8000/users/me/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Testing

Run the comprehensive test suite:
```bash
python test_auth_integration.py
```

## Troubleshooting

### API won't start
- Check if all dependencies are installed: `pip install -r requirements.txt`
- Try installing Supabase separately: `pip install supabase`

### "No authentication provider available"
- Configure Supabase or Firebase in `.env`
- See `HOW_TO_REGISTER.md` for configuration details

### "User already exists"
- Email is already registered
- Try logging in instead or use different email

## Next Steps

1. ✅ Start the API: `python api.py`
2. ✅ Configure `.env` with auth provider
3. ✅ Register a user: `python register_user_example.py`
4. ✅ Login to get access token
5. ✅ Use protected endpoints to generate layouts

## Documentation

- **`HOW_TO_REGISTER.md`** - Detailed registration guide
- **`register_user_example.py`** - Interactive script
- **`test_auth_integration.py`** - Test all auth features
- **`.env.example`** - Configuration template
