# database.py
import os
import random

from pymongo import MongoClient
from typing import List
from passlib.context import CryptContext
from app.advertisement.service import database as ad_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

client = MongoClient(os.getenv("MONGO_URI"))
db = client["dev"]


def select_random_coupon_code(advertisement_id: str):
    # Retrieve all available coupon codes for the advertisement
    advertisement_coupons = list(
        db.coupons.find(
            {"advertisement_id": advertisement_id, "user_email": {"$exists": False}}
        )
    )
    coupon_codes = [coupon["code"] for coupon in advertisement_coupons]

    # Select a random coupon code
    if coupon_codes:
        return random.choice(coupon_codes)
    else:
        return None


def mark_coupon_code_as_used(
    advertisement_id: str, coupon_code: str, email_address: str
):
    db.coupons.update_one(
        {"advertisement_id": advertisement_id, "code": coupon_code},
        {"$set": {"user_email": email_address}},
    )
    # Check if the coupon was the last remaining one for the advertisement
    remaining_coupons = db.coupons.count_documents(
        {"advertisement_id": advertisement_id, "user_email": {"$exists": False}}
    )
    if remaining_coupons == 0:
        # Update advertisement to mark it as closed
        ad_db.close_advertisement(advertisement_id)


def get_user_coupons(email_address: str):
    coupons = list(db.coupons.find({"user_email": email_address}, {"_id": 0}))
    return coupons


def add_coupon(coupon: dict):
    db.coupons.insert_one(coupon)


def get_ad_coupons(advertisement_id: str):
    coupons = list(db.coupons.find({"advertisement_id": advertisement_id}))
    return coupons


def add_coupons(coupons: List[dict]):
    db.coupons.insert_many(coupons)


def check_if_user_already_has_coupon(advertisement_id: str, email_address):
    coupon = db.coupons.find_one(
        {"advertisement_id": advertisement_id, "user_email": email_address}
    )
    if coupon:
        return True
    else:
        return False
