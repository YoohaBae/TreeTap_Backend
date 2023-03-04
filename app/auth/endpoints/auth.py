import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from passlib.context import CryptContext
from app.auth.service import database
from app.auth.models.user import UserCreate, User
from app.advertisement.service import database as ad_db
from app.utils.utils import get_current_user, create_access_token

router = APIRouter()

# Token expiration time (in minutes)
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Initialize password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# OAuth2 authentication scheme


def authenticate_user(emailAddress: str, password: str):
    user = database.get_user(emailAddress)
    if not user:
        return False
    if not pwd_context.verify(password, user.hashed_password):
        return False
    return user





@router.post("/signup", tags=["auth"], status_code=status.HTTP_201_CREATED)
def sign_up(user: UserCreate):
    # Check if user already exists in the database
    if database.user_exists(user.emailAddress):
        raise HTTPException(status_code=400, detail="User already registered")

    # If user does not exist, add user to the database
    database.create_user(user)

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


@router.post("/plant", tags=["profile"])
def plant_tree(advertisement_id: str, current_user: User = Depends(get_current_user)):
    advertisement = ad_db.get_advertisement(advertisement_id)
    trees_per_click = advertisement.get("trees_per_click", 1)
    ad_db.increase_trees_planted_in_advertisement(advertisement_id, trees_per_click)
    database.plant_tree(current_user.emailAddress, trees_per_click)
    return {"message": "Trees planted successfully"}
