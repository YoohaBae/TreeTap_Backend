# database.py
import os

from pymongo import MongoClient
from passlib.context import CryptContext
from bson import ObjectId

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

client = MongoClient(os.getenv("MONGO_URI"))
db = client["dev"]


def add_advertisement(advertisement):
    # Insert new advertisement object into the database
    db.advertisements.insert_one(advertisement)


def get_advertisement(advertisement_id):
    advertisement = db.advertisements.find_one({"_id": ObjectId(advertisement_id)})
    return advertisement


def approve_advertisement(advertisement_id):
    # Update the advertisement to set the approved field to True
    db.advertisements.update_one(
        {"_id": ObjectId(advertisement_id)}, {"$set": {"approved": True}}
    )
