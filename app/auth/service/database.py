# database.py
import os

from pymongo import MongoClient
from app.auth.models.user import UserCreate, User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db_user_name = os.getenv("MONGODB_USER")
db_password = os.getenv("MONGODB_PW")
client = MongoClient(f"mongodb+srv://{db_user_name}:{db_password}@treetap.9wqqzyq.mongodb.net/?retryWrites=true&w=majority")
db = client["mydatabase"]


def get_user(emailAddress: str):
    user_data = db.users.find_one({"emailAddress": emailAddress})
    if user_data:
        return User(**user_data)
    return None


def create_user(user: UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db.users.insert_one({"emailAddress": user.emailAddress, "hashed_password": hashed_password})


def user_exists(emailAddress: str):
    return db.users.find_one({"emailAddress": emailAddress}) is not None
