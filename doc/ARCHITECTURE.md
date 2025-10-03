# Bathroom Layout Generator API - Architecture

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Flutter Client                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Login Screen │  │ Layout Screen│  │ History Screen│          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
│         └──────────────────┴──────────────────┘                  │
│                            │                                      │
│                    ┌───────▼────────┐                            │
│                    │ API Client     │                            │
│                    │ (auth_example) │                            │
│                    └───────┬────────┘                            │
└────────────────────────────┼─────────────────────────────────────┘
                             │ HTTP/HTTPS
                             │ JSON + JWT Token
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│                      FastAPI Server (api.py)                      │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Public Endpoints                       │    │
│  │  • GET  /                    (Health Check)             │    │
│  │  • POST /api/generate        (Generate Layout)          │    │
│  │  • GET  /api/layout/{id}     (Get Layout)               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Authentication Endpoints                    │    │
│  │  • POST /users/              (Register)                 │    │
│  │  • POST /token               (Login)                    │    │
│  │  • GET  /users/me/           (Get User)                 │    │
│  │  • POST /auth/firebase/verify-token                     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Protected Endpoints                         │    │
│  │  • POST   /api/protected/generate                       │    │
│  │  • GET    /api/protected/layouts/                       │    │
│  │  • GET    /api/protected/layout/{id}                    │    │
│  │  • DELETE /api/protected/layout/{id}                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │  user_api.py     │  │  Middleware      │                     │
│  │  • JWT Auth      │  │  • CORS          │                     │
│  │  • User Models   │  │  • Auth Check    │                     │
│  │  • Token Mgmt    │  │                  │                     │
│  └────────┬─────────┘  └──────────────────┘                     │
│           │                                                       │
└───────────┼───────────────────────────────────────────────────────┘
            │
            ├─────────────────┬─────────────────┬──────────────────┐
            │                 │                 │                  │
            ▼                 ▼                 ▼                  ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────┐
    │  Supabase    │  │  Firebase    │  │  Layout      │  │  Data   │
    │  Auth        │  │  Auth        │  │  Generator   │  │  Store  │
    │              │  │              │  │  (Beam       │  │  (JSON/ │
    │  • Users     │  │  • Users     │  │   Search)    │  │   PKL)  │
    │  • Sessions  │  │  • OAuth     │  │              │  │         │
    └──────────────┘  └──────────────┘  └──────────────┘  └─────────┘
```

## Authentication Flow

```
┌──────────┐                                      ┌──────────┐
│  Client  │                                      │   API    │
└────┬─────┘                                      └────┬─────┘
     │                                                 │
     │  1. POST /token                                │
     │    (email, password)                           │
     ├───────────────────────────────────────────────►│
     │                                                 │
     │                                    2. Validate │
     │                                       with     │
     │                                       Supabase/│
     │                                       Firebase │
     │                                                 │
     │  3. Return JWT Token                           │
     │◄───────────────────────────────────────────────┤
     │    {access_token, token_type, provider}        │
     │                                                 │
     │  4. Store Token                                │
     │    (SharedPreferences/SecureStorage)           │
     │                                                 │
     │  5. POST /api/protected/generate               │
     │    Authorization: Bearer <token>               │
     ├───────────────────────────────────────────────►│
     │                                                 │
     │                                    6. Validate │
     │                                       JWT Token│
     │                                                 │
     │                                    7. Extract  │
     │                                       User Info│
     │                                                 │
     │                                    8. Generate │
     │                                       Layout   │
     │                                                 │
     │                                    9. Associate│
     │                                       with User│
     │                                                 │
     │  10. Return Layout                             │
     │◄───────────────────────────────────────────────┤
     │     {layout_id, score, objects, ...}           │
     │                                                 │
```

## Data Flow - Layout Generation

```
┌─────────────────────────────────────────────────────────────────┐
│                     Layout Generation Flow                       │
└─────────────────────────────────────────────────────────────────┘

1. Client Request
   ├─ Room Dimensions (width, depth, height)
   ├─ Objects to Place (toilet, sink, shower, etc.)
   ├─ Windows/Doors (position, size, wall)
   └─ Beam Width (search thoroughness)
        │
        ▼
2. Authentication Check (if protected endpoint)
   ├─ Validate JWT Token
   ├─ Extract User ID
   └─ Check User Status
        │
        ▼
3. Bathroom Model Creation
   ├─ Create Bathroom instance
   ├─ Add Windows/Doors
   └─ Set Constraints
        │
        ▼
4. Beam Search Algorithm
   ├─ Initialize Beam
   ├─ Generate Candidate Layouts
   ├─ Score Each Layout
   │   ├─ No Overlap
   │   ├─ Wall/Corner Constraints
   │   ├─ Spacing
   │   ├─ Accessibility
   │   └─ Other Criteria
   ├─ Keep Top N Layouts
   └─ Iterate Until Complete
        │
        ▼
5. Select Best Layout
   ├─ Highest Score
   ├─ All Constraints Met
   └─ Accessibility Score ≥ 4
        │
        ▼
6. Store Layout
   ├─ In-Memory Cache
   ├─ JSON File (before/after states)
   ├─ Pickle File (Python objects)
   └─ Associate with User (if authenticated)
        │
        ▼
7. Return Response
   ├─ Layout ID
   ├─ Score & Breakdown
   ├─ Object Positions
   ├─ Processing Time
   └─ Windows/Doors
```

## Component Interaction

```
┌─────────────────────────────────────────────────────────────────┐
│                        api.py (Main API)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    user_api.py                            │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  Authentication Functions                          │  │   │
│  │  │  • create_access_token()                           │  │   │
│  │  │  • verify_password()                               │  │   │
│  │  │  • get_current_user()                              │  │   │
│  │  │  • get_current_active_user()                       │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                                                            │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  Route Setup                                       │  │   │
│  │  │  • setup_user_api_routes(app)                      │  │   │
│  │  │    ├─ POST /token                                  │  │   │
│  │  │    ├─ POST /users/                                 │  │   │
│  │  │    ├─ GET  /users/me/                              │  │   │
│  │  │    └─ POST /logout                                 │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                                                            │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  External Auth Integration                         │  │   │
│  │  │  • Supabase Client                                 │  │   │
│  │  │  • Firebase Admin SDK                              │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Layout Generation Components                 │   │
│  │  • models/bathroom.py      (Bathroom Model)              │   │
│  │  • models/object.py        (Object Models)               │   │
│  │  • models/layout.py        (Layout Model)                │   │
│  │  • algorithms/beam_search.py (Search Algorithm)          │   │
│  │  • optimization/scoring.py   (Scoring Functions)         │   │
│  │  • utils/helpers.py          (Helper Functions)          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Security Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                         Security Layers                          │
└─────────────────────────────────────────────────────────────────┘

Layer 1: Transport Security
├─ HTTPS (Production)
├─ CORS Configuration
└─ Request Size Limits

Layer 2: Authentication
├─ JWT Token Validation
├─ Token Expiration (30 min default)
├─ Secure Token Storage (Client)
└─ Password Hashing (Bcrypt)

Layer 3: Authorization
├─ User Ownership Verification
├─ Protected Endpoint Guards
├─ Role-Based Access (Future)
└─ Resource-Level Permissions

Layer 4: Data Validation
├─ Pydantic Models
├─ Input Sanitization
├─ Type Checking
└─ Constraint Validation

Layer 5: Error Handling
├─ Generic Error Messages
├─ No Sensitive Data Leakage
├─ Proper HTTP Status Codes
└─ Logging (Without Secrets)
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Production Deployment                       │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐
│   Internet   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Load Balancer│
│   (HTTPS)    │
└──────┬───────┘
       │
       ├─────────────────┬─────────────────┐
       ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  API Server  │  │  API Server  │  │  API Server  │
│   Instance 1 │  │   Instance 2 │  │   Instance 3 │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┴─────────────────┘
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
       ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Supabase   │  │   Firebase   │  │    Redis     │
│   Database   │  │     Auth     │  │    Cache     │
└──────────────┘  └──────────────┘  └──────────────┘
```

## File Structure

```
streamlit_app/
├── api.py                          # Main API with auth integration
├── user_api.py                     # Authentication system
├── example_protected_api.py        # Integration examples
├── test_auth_integration.py        # Test suite
│
├── models/
│   ├── bathroom.py                 # Bathroom model
│   ├── object.py                   # Object models
│   └── layout.py                   # Layout model
│
├── algorithms/
│   └── beam_search.py              # Layout generation algorithm
│
├── optimization/
│   └── scoring.py                  # Layout scoring functions
│
├── utils/
│   └── helpers.py                  # Helper utilities
│
├── flutter_integration_example/
│   ├── auth_example.dart           # Flutter auth client
│   └── bathroom_api_client.dart    # API client
│
├── data/
│   └── layout_states/              # Saved layout states
│
├── .env                            # Environment variables (gitignored)
├── .env.example                    # Environment template
├── requirements.txt                # Python dependencies
│
└── Documentation/
    ├── API_DOCUMENTATION.md        # Complete API reference
    ├── USER_API_README.md          # Auth documentation
    ├── AUTHENTICATION_QUICK_START.md # Quick start guide
    ├── INTEGRATION_SUMMARY.md      # Integration summary
    ├── ARCHITECTURE.md             # This file
    └── UPDATES.md                  # Change log
```

## Technology Stack

```
Backend:
├── FastAPI          (Web framework)
├── Pydantic         (Data validation)
├── Python-Jose/JWT  (Token management)
├── Passlib          (Password hashing)
├── Uvicorn          (ASGI server)
└── Python 3.8+      (Runtime)

Authentication:
├── Supabase         (Primary auth provider)
├── Firebase         (Alternative auth provider)
└── JWT              (Token format)

Frontend:
├── Flutter          (Mobile/Web framework)
├── Dart             (Programming language)
└── HTTP Package     (API client)

Data Storage:
├── In-Memory Dict   (Current - layout cache)
├── JSON Files       (Layout states)
├── Pickle Files     (Python objects)
└── PostgreSQL       (Future - via Supabase)
```

This architecture provides a scalable, secure, and maintainable system for bathroom layout generation with user authentication.
