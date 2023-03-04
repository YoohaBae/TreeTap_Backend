from pydantic import BaseModel


class User(BaseModel):
    emailAddress: str
    hashed_password: str


class UserCreate(BaseModel):
    emailAddress: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
