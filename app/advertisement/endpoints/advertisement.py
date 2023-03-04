import os
import uuid
from enum import Enum
from typing import List
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form,
    Body,
    Response,
    Query,
)
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.utils.utils import get_current_user
from app.auth.models.user import User
from app.advertisement.service import database
from app.auth.service import coupon_db

router = APIRouter()

UPLOAD_DIR = "uploads"

server_email = os.getenv("EMAIL_ADDRESS")
server_email_password = os.getenv("EMAIL_PASSWORD")
admin_email = os.getenv("ADMIN_EMAIL")

# Mail connection configuration
conf = ConnectionConfig(
    MAIL_USERNAME=server_email,
    MAIL_PASSWORD=server_email_password,
    MAIL_FROM="treetap.yyy@gmail.com",
    MAIL_PORT=465,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
)


class MediaTypeEnum(str, Enum):
    png = "image/png"
    jpg = "image/jpeg"


# Create FastMail instance
mail = FastMail(conf)


@router.post("/register", tags=["advertisement"])
async def request_advertisement(
    company_name: str = Form(...),
    website: str = Form(...),
    coupon_info: str = Form(...),
    trees_per_click: int = Form(...),
    advertisement_content: str = Form(...),
    advertisement_image: UploadFile = File(
        ..., media_type=str([MediaTypeEnum.png, MediaTypeEnum.jpg])
    ),
    current_user: User = Depends(get_current_user),
):
    # Create new advertisement object
    advertisement = {
        "company_name": company_name,
        "website": website,
        "coupon_info": coupon_info,
        "trees_per_click": trees_per_click,
        "advertisement_content": advertisement_content,
        "created_by": current_user.emailAddress,
        "approved": False,
        "closed": False,
    }

    # Save the uploaded image to the file system
    file_extension = os.path.splitext(advertisement_image.filename)[1]
    unique_filename = str(uuid.uuid4()) + file_extension
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    with open(file_path, "wb") as f:
        f.write(advertisement_image.file.read())

    # Add the file path to the advertisement object
    advertisement["advertisement_image"] = file_path

    # Insert new advertisement object into the database
    database.add_advertisement(advertisement)
    # Send notification email to the specified email address
    message = MessageSchema(
        subject="New Advertisement Created",
        recipients=[admin_email],
        body=f"Dear Admin,\n\nA new advertisement has been created by {current_user.emailAddress}."
        f"\n\nCompany Name: {company_name}\nWebsite: {website}\nCoupon Info: {coupon_info}\n"
        f"Trees per Click: {trees_per_click}\nAdvertisement Content: {advertisement_content}\n\n"
        f"Best regards,\nTree Tap YYY",
        subtype="plain",
    )
    await mail.send_message(message)

    # Send confirmation email to the user
    user_message = MessageSchema(
        subject="Advertisement Request Received",
        recipients=[current_user.emailAddress],
        body=f"Dear {current_user.emailAddress},\n\nThank you for submitting your advertisement request. "
        f"We have received your request and will review your advertisement soon. We will be in advertisement "
        f"with you shortly regarding the status of your request.\n\nBest regards,\nTree Tap YYY",
        subtype="plain",
    )
    await mail.send_message(user_message)

    return {"message": "Advertisement created successfully"}


@router.post("/{advertisement_id}/approve", tags=["advertisement"])
async def approve_advertisement(
    advertisement_id: str,
    ngo: str,
    coupon_codes: List[str] = Body(default=[]),
    current_user: User = Depends(get_current_user),
):
    # Retrieve the advertisement from the database
    advertisement = database.get_advertisement(advertisement_id)
    if not advertisement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Advertisement not found"
        )

    # Check if the current user is authorized to approve the advertisement
    if current_user.emailAddress != admin_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Only administrators can approve advertisements",
        )

    # Check if the coupon codes are valid and not duplicates
    if len(coupon_codes) != len(set(coupon_codes)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate coupon codes"
        )

    database.approve_advertisement(advertisement_id, ngo)

    # Add coupon codes to the coupons collection
    for code in coupon_codes:
        coupon = {"advertisement_id": advertisement_id, "code": code}
        coupon_db.add_coupon(coupon)

    # Send notification email to the advertiser
    advertiser_email = advertisement["created_by"]
    message = MessageSchema(
        subject="Advertisement Approved",
        recipients=[advertiser_email],
        body="Dear Advertiser,\n\nYour advertisement has been approved and is now live. "
        "Thank you for using our service!\n\nBest regards,\nTree Tap",
        subtype="plain",
    )
    await mail.send_message(message)

    return {"message": "Advertisement approved successfully"}


@router.get("/admin", tags=["advertisement"])
async def get_all_advertisements(current_user: User = Depends(get_current_user)):
    # Check if the current user is authorized to access the advertisements
    if current_user.emailAddress != admin_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Only administrators can access advertisements",
        )

    advertisements = database.get_all_advertisements()
    # Convert binary image data to base64-encoded string
    for advertisement in advertisements:
        advertisement["_id"] = str(advertisement["_id"])
        advertisement["advertisement_content"] = advertisement[
            "advertisement_content"
        ].replace("\\n", "")

    return advertisements


@router.get("/", tags=["advertisement"])
async def get_approved_advertisements(current_user: User = Depends(get_current_user)):
    # Retrieve approved advertisements from MongoDB
    approved_advertisements = database.get_approved_advertisements()

    # Convert binary image data to base64-encoded string
    for advertisement in approved_advertisements:
        advertisement["_id"] = str(advertisement["_id"])
        advertisement["advertisement_content"] = advertisement[
            "advertisement_content"
        ].replace("\\n", "")
        exists = coupon_db.check_if_user_already_has_coupon(
            advertisement["_id"], current_user.emailAddress
        )
        if exists:
            advertisement["already_done"] = True
        else:
            advertisement["already_done"] = False
    return approved_advertisements


@router.get("/images")
async def get_image(file_name: str):
    image_full_path = os.path.join(os.getcwd(), file_name)
    if os.path.exists(image_full_path):
        with open(image_full_path, "rb") as image_file:
            return Response(content=image_file.read(), media_type="image/png")
    else:
        raise HTTPException(status_code=404, detail="Image not found")


@router.put("/{advertisement_id}", tags=["advertisement"])
async def close_advertisement(
    advertisement_id: str, current_user: User = Depends(get_current_user)
):
    # Check if the current user is authorized to approve the advertisement
    if current_user.emailAddress != admin_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Only administrators can approve advertisements",
        )

    # Update the advertisement to set the closed field to True
    database.close_advertisement(advertisement_id)
    return {"message": "Advertisement closed successfully"}


@router.put("/{advertisement_id}/coupons", tags=["coupons"])
def refill_coupons(advertisement_id: str, coupon_codes: List[str] = Body(default=[])):
    advertisement = database.get_advertisement(advertisement_id)
    if not advertisement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Advertisement not found"
        )

    current_coupons = coupon_db.get_ad_coupons(advertisement_id)
    current_coupon_codes = [c["code"] for c in current_coupons]

    # Check if any of the new coupon numbers already exist
    duplicates = set(current_coupon_codes) & set(coupon_codes)
    if duplicates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Duplicate coupon numbers: {', '.join(duplicates)}",
        )
    # Add the new coupon codes to the database
    new_coupons = [
        {"advertisement_id": advertisement_id, "coupon_code": c} for c in coupon_codes
    ]
    coupon_db.add_coupons(new_coupons)
    return {"message": f"{len(new_coupons)} coupon codes added successfully"}


@router.get("/filter", tags=["advertisement"])
async def get_advertisements_of_ids(
    advertisement_ids: str = Query(None), current_user: User = Depends(get_current_user)
):
    if advertisement_ids is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing advertisement_ids parameter",
        )

    advertisement_ids = advertisement_ids.split(",")
    approved_advertisements = database.get_approved_advertisements_by_ids(
        advertisement_ids
    )
    return approved_advertisements
