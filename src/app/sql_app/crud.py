import json, os
from shutil import rmtree
from fastapi import status, HTTPException
from redis.asyncio import Redis
from aiofiles import os as aiofiles_os

from ..constants import PATH_FILES
from ..schemas.users import UserInDB


async def get_user(db: Redis, username: str) -> UserInDB:
    data = await db.get(username)
    if data:
        user_dict = json.loads(data)
        return UserInDB(**user_dict)


async def create_user(db: Redis, username: str, value: str):
    path_to_dir = os.path.join(PATH_FILES, username)
    dir_exists = await aiofiles_os.path.isdir(path_to_dir)
    if dir_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User already exists')
    else:
        await aiofiles_os.mkdir(path_to_dir)
        await db.set(username, value)


async def update_user(db: Redis, delete_username: str, new_username: str, new_value: str):
    await aiofiles_os.replace(os.path.join(PATH_FILES, delete_username), os.path.join(PATH_FILES, new_username))
    await db.delete(delete_username)
    await db.set(new_username, new_value)


async def delete_user(db: Redis, username: str):
    path_to_dir= os.path.join(PATH_FILES, username)
    dir_exists = await aiofiles_os.path.isdir(path_to_dir)
    if not dir_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User haven\'t exists')
    else:
        rmtree(os.path.join(PATH_FILES, username))
        await db.delete(username)
