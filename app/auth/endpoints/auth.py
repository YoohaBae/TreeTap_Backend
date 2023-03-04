# main.py
import os
import datetime
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from app.auth.service.database import get_user, create_user, user_exists
from app.auth.models.user import UserCreate, User

router = APIRouter()

# Secret key for JWT token
SECRET_KEY = os.getenv("SECRET_KEY")

# Algorithm used for JWT token encoding
ALGORITHM = "HS256"

# Token expiration time (in minutes)
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Initialize password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 authentication scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def authenticate_user(emailAddress: str, password: str):
    user = get_user(emailAddress)
    if not user:
        return False
    if not pwd_context.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: datetime.timedelta):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        emailAddress: str = payload.get("sub")
        if emailAddress is None:
            raise HTTPException(
                status_code=401, detail="Invalid authentication credentials"
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = get_user(emailAddress)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return user


@router.post("/signup", tags=["auth"], status_code=status.HTTP_201_CREATED)
def sign_up(user: UserCreate):
    # Check if user already exists in the database
    if user_exists(user.emailAddress):
        raise HTTPException(status_code=400, detail="User already registered")

    # If user does not exist, add user to the database
    create_user(user)

    return {"message": "User registered successfully"}


@router.post("/login", tags=["auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.emailAddress}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/protected", tags=["auth"])
def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": "You are still logged in"}
