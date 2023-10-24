import asyncio, os, pytest
from pathlib import Path

from aiofiles import os as aiofiles_os
from fastapi import HTTPException
from datetime import timedelta

from src.app.schemas.users import UserInDB
from src.app.sql_app.crud import create_user, delete_user
from src.app.dependencies import get_password_hash, get_db, create_access_token
from src.app.constants import ACCESS_TOKEN_EXPIRE_MINUTES, BASE_DIR

test_admin_username = os.environ['TEST_ADMIN_USERNAME'] or None
test_admin_password = os.environ['TEST_ADMIN_PASSWORD'] or None
test_admin_email = os.environ['TEST_ADMIN_EMAIL'] or None
test_admin_full_name = os.environ['TEST_ADMIN_FULL_NAME'] or None

test_client_username = os.environ['TEST_CLIENT_USERNAME'] or None
test_client_password = os.environ['TEST_CLIENT_PASSWORD'] or None
test_client_email = os.environ['TEST_CLIENT_EMAIL'] or None
test_client_full_name = os.environ['TEST_CLIENT_FULL_NAME'] or None

test_admin_user = UserInDB(
    username=test_admin_username,
    email=test_admin_email,
    full_name=test_admin_full_name,
    hashed_password=get_password_hash(test_admin_password),
    admin=True,
)
test_client_user = UserInDB(
    username=test_client_username,
    email=test_client_email,
    full_name=test_client_full_name,
    hashed_password=get_password_hash(test_client_password),
)

test_admin_user.__dict__['password'] = test_admin_password
test_client_user.__dict__['password'] = test_client_password

test_admin_user.__dict__['token'] = create_access_token(
    data={"sub": test_admin_user.username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
)
test_client_user.__dict__['token'] = create_access_token(
    data={"sub": test_client_user.username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
)

base_dir = Path(__file__).resolve().parent.parent

files = [
    ('files', (open(os.path.join(base_dir / 'tests', 'csv_files', 'organizations.csv'), 'rb'))),
    ('files', (open(os.path.join(base_dir / 'tests', 'csv_files', 'people.csv'), 'rb')))
]


def get_headers_dict(access_token: str | None = None) -> dict:
    return {'Authorization': 'Bearer ' + access_token} if access_token else {}


async def start():
    db = await anext(get_db())

    try:
        await delete_user(db, test_admin_user.username)
    except HTTPException as exp:
        pass
    try:
        await delete_user(db, test_client_user.username)
    except HTTPException as exp:
        pass

    try:
        await delete_user(db, 'new_username1')
    except HTTPException as exp:
        pass
    try:
        await delete_user(db, 'new_username2')
    except HTTPException as exp:
        pass

    await create_user(db, test_admin_user.username, test_admin_user.model_dump_json())
    await create_user(db, test_client_user.username, test_client_user.model_dump_json())


try:
    asyncio.run(start())
except KeyboardInterrupt as exp:
    print('exit event loop')
