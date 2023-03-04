import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.auth.endpoints.auth import get_current_user
from app.auth.models.user import User
from app.contact.service.database import (
    add_advertisement,
    get_advertisement,
    approve_advertisement,
)


router = APIRouter()

email = os.getenv("EMAIL_ADDRESS")
email_password = os.getenv("EMAIL_PASSWORD")
admin_email = os.getenv("ADMIN_EMAIL")


# Mail connection configuration
conf = ConnectionConfig(
    MAIL_USERNAME=email,
    MAIL_PASSWORD=email_password,
    MAIL_FROM="treetap.yyy@gmail.com",
    MAIL_PORT=465,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
)

# Create FastMail instance
mail = FastMail(conf)


@router.post("/register", tags=["contact"])
async def request_advertisement(
    company_name: str = Form(...),
    website: str = Form(...),
    coupon_info: str = Form(...),
    trees_per_click: int = Form(...),
    advertisement_content: str = Form(...),
    advertisement_image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    # Read image file contents
    image_file = advertisement_image.file.read()

    # Create new advertisement object
    advertisement = {
        "company_name": company_name,
        "website": website,
        "coupon_info": coupon_info,
        "trees_per_click": trees_per_click,
        "advertisement_content": advertisement_content,
        "advertisement_image": image_file,
        "created_by": current_user.emailAddress,
        "approved": False,
    }

    # Insert new advertisement object into the database
    add_advertisement(advertisement)
    # Send notification email to the specified email address
    message = MessageSchema(
        subject="New Advertisement Created",
        recipients=[admin_email],
        body=f"Dear Admin,\n\nA new advertisement has been created by {current_user.emailAddress}."
        f"\n\nCompany Name: {company_name}\nWebsite: {website}\nCoupon Info: {coupon_info}\n"
        f"Trees per Click: {trees_per_click}\nAdvertisement Content: {advertisement_content}\n\n"
        f"Best regards,\nYour Application",
        subtype="plain",
    )
    await mail.send_message(message)

    # Send confirmation email to the user
    user_message = MessageSchema(
        subject="Advertisement Request Received",
        recipients=[email],
        body=f"Dear {current_user.emailAddress},\n\nThank you for submitting your advertisement request. "
        f"We have received your request and will review your advertisement soon. We will be in contact "
        f"with you shortly regarding the status of your request.\n\nBest regards,\nYour Application",
        subtype="plain",
    )
    await mail.send_message(user_message)

    return {"message": "Advertisement created successfully"}


@router.post("/advertisements/{advertisement_id}/approve", tags=["contact"])
async def post_approve_ad(
    advertisement_id: str, current_user: User = Depends(get_current_user)
):
    # Retrieve the advertisement from the database
    advertisement = get_advertisement(advertisement_id)
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

    approve_advertisement(advertisement_id)

    # Send notification email to the advertiser
    advertiser_email = advertisement["email"]
    message = MessageSchema(
        subject="Advertisement Approved",
        recipients=[advertiser_email],
        body="Dear Advertiser,\n\nYour advertisement has been approved and is now live. "
        "Thank you for using our service!\n\nBest regards,\nTree Tap",
        subtype="plain",
    )
    await mail.send_message(message)

    return {"message": "Advertisement approved successfully"}
