from pydantic import BaseModel, EmailStr


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None
    admin: bool | None = None


class UserInCreate(BaseModel):
    username: str
    password: str
    email: EmailStr | None = None
    full_name: str | None = None


class UserInUpdate(UserInCreate):
    username: str | None = None
    password: str | None = None


class UserInDB(User):
    hashed_password: str
