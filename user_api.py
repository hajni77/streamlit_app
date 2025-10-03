from fastapi import FastAPI, HTTPException, Depends, status, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any
import os
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import jwt
from passlib.context import CryptContext

# Optional imports - handle gracefully if not available
try:
    import firebase_admin
    from firebase_admin import credentials, auth
    FIREBASE_AVAILABLE = True
except ImportError:
    print("Warning: Firebase not available. Install firebase-admin to use Firebase authentication.")
    FIREBASE_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not available. Using environment variables directly.")

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    print("Warning: Supabase not available. Install supabase to use Supabase authentication.")
    SUPABASE_AVAILABLE = False
    Client = None

# Initialize Firebase if available
if FIREBASE_AVAILABLE and not len(firebase_admin._apps):
    try:
        # Try to load from JSON file
        if os.path.exists("firebase_credentials.json"):
            cred = credentials.Certificate("firebase_credentials.json")
            firebase_admin.initialize_app(cred)
        # If not available, try to use base64 encoded credentials from env var
        elif os.getenv("FIREBASE_CREDENTIALS_BASE64"):
            import base64
            cred_json = base64.b64decode(os.getenv("FIREBASE_CREDENTIALS_BASE64")).decode('utf-8')
            cred = credentials.Certificate(json.loads(cred_json))
            firebase_admin.initialize_app(cred)
        else:
            print("Warning: Firebase credentials not found")
            FIREBASE_AVAILABLE = False
    except Exception as e:
        print(f"Error initializing Firebase: {str(e)}")
        FIREBASE_AVAILABLE = False

# Initialize Supabase client if available
supabase = None
if SUPABASE_AVAILABLE:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if supabase_url and supabase_key:
        try:
            supabase = create_client(supabase_url, supabase_key)
        except Exception as e:
            print(f"Error initializing Supabase: {str(e)}")
            supabase = None
    else:
        print("Warning: SUPABASE_URL or SUPABASE_KEY not set in environment")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")  # In production, use a secure key from env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 password bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# User models
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: str
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.now)
    disabled: bool = False

class User(UserBase):
    id: str
    disabled: bool = False

class Token(BaseModel):
    access_token: str
    token_type: str
    provider: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[str] = None

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        if email is None or user_id is None:
            raise credentials_exception
        token_data = TokenData(email=email, user_id=user_id)
    except jwt.PyJWTError:
        raise credentials_exception
    
    # Here you would typically fetch the user from your database
    # For now, we'll use a stub implementation
    user = User(id=user_id, email=email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# API routes for user management
def setup_user_api_routes(app: FastAPI):
    @app.post("/token", response_model=Token)
    async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
        """
        OAuth2 compatible token login, get an access token for future requests
        """
        auth_error = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            # Try with Supabase if available
            if supabase:
                try:
                    response = supabase.auth.sign_in_with_password({
                        "email": form_data.username,
                        "password": form_data.password
                    })
                    if response and hasattr(response, 'session'):
                        user_id = response.user.id
                        access_token = response.session.access_token
                        return {"access_token": access_token, "token_type": "bearer", "provider": "supabase"}
                except Exception as e:
                    print(f"Supabase auth error: {str(e)}")
                    # Continue to next auth method
            
            # Fallback to Firebase auth if available
            if FIREBASE_AVAILABLE:
                try:
                    user = auth.get_user_by_email(form_data.username)
                    # Note: Firebase Admin SDK can't verify passwords directly
                    # This is typically handled by Firebase Authentication client SDK
                    # Here we're just simulating success for a valid email
                    user_id = user.uid
                    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                    access_token = create_access_token(
                        data={"sub": form_data.username, "user_id": user_id},
                        expires_delta=access_token_expires
                    )
                    return {"access_token": access_token, "token_type": "bearer", "provider": "firebase"}
                except Exception as e:
                    print(f"Firebase auth error: {str(e)}")
            
            # If all auth methods fail
            raise auth_error
            
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            raise auth_error

    @app.post("/users/", response_model=User)
    async def create_user(user: UserCreate):
        """
        Create a new user with the provided email and password
        """
        try:
            # Try to create user with Supabase if available
            if supabase:
                try:
                    response = supabase.auth.sign_up({
                        "email": user.email,
                        "password": user.password,
                        "options": {
                            "data": {
                                "full_name": user.full_name
                            }
                        }
                    })
                    if response and hasattr(response, 'user'):
                        return {
                            "id": response.user.id,
                            "email": user.email,
                            "full_name": user.full_name
                        }
                except Exception as e:
                    print(f"Supabase user creation error: {str(e)}")
            
            # Fallback to Firebase if available
            if FIREBASE_AVAILABLE:
                try:
                    user_record = auth.create_user(
                        email=user.email,
                        password=user.password,
                        display_name=user.full_name
                    )
                    return {
                        "id": user_record.uid,
                        "email": user.email,
                        "full_name": user.full_name
                    }
                except Exception as e:
                    print(f"Firebase user creation error: {str(e)}")
            
            # If no auth provider is available
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No authentication provider available. Please configure Supabase or Firebase."
            )
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User creation failed: {str(e)}"
            )

    @app.get("/users/me/", response_model=User)
    async def read_users_me(current_user: User = Depends(get_current_active_user)):
        """
        Get information about the currently authenticated user
        """
        return current_user

    @app.post("/auth/firebase/verify-token")
    async def verify_firebase_token(request: Request):
        """
        Verify a Firebase ID token
        """
        try:
            body = await request.json()
            id_token = body.get("idToken")
            if not id_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ID token is required"
                )
            
            # Verify the token with Firebase
            decoded_token = auth.verify_id_token(id_token)
            user_id = decoded_token['uid']
            
            # Generate a session token for our API
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": decoded_token.get("email", ""), "user_id": user_id},
                expires_delta=access_token_expires
            )
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user_id": user_id,
                "email": decoded_token.get("email")
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication credentials: {str(e)}"
            )

    @app.post("/logout")
    async def logout(response: Response, current_user: User = Depends(get_current_user)):
        """
        Logout the current user by invalidating the token
        Note: JWT tokens can't be truly invalidated without a blacklist/database
        """
        # Here you would typically add the token to a blacklist
        # or revoke sessions in Supabase/Firebase
        response.delete_cookie(key="access_token")
        return {"message": "Successfully logged out"}

# To use this in your main FastAPI application:
# from user_api import setup_user_api_routes
# setup_user_api_routes(app)  # where app is your FastAPI instance
