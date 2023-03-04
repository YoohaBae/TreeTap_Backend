import jwt
import datetime
import os
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.auth.service import database

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
# Secret key for JWT token
SECRET_KEY = os.getenv("SECRET_KEY")
# Algorithm used for JWT token encoding
ALGORITHM = "HS256"


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
    user = database.get_user(emailAddress)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return user
