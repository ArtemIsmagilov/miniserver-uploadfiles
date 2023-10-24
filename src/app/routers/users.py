from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis

from ..dependencies import get_current_active_user, get_password_hash, get_db
from ..schemas.users import UserInUpdate, User, UserInCreate, UserInDB
from ..sql_app.crud import create_user, delete_user, update_user, get_user

router = APIRouter(
    prefix='/users',
    tags=['users'],
)


@router.get("/{username}", response_model=User)
async def read_user(
        current_user: Annotated[User, Depends(get_current_active_user)],
        db: Annotated[Redis, Depends(get_db)],
        username: str,
):
    if username == 'me':
        username = current_user.username
    user = await get_user(db, username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User doesn\'t exists')
    return user


@router.put("/{username}", response_model=User)
async def patch_user(
        current_user: Annotated[User, Depends(get_current_active_user)],
        db: Annotated[Redis, Depends(get_db)],
        patched_user: UserInUpdate,
        username: str,
):
    if username == 'me':
        username = current_user.username
    elif username != current_user.username and not current_user.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Requires admin privileges')

    update_data = patched_user.model_dump(exclude_unset=True)
    password = update_data.pop('password', None)
    if password:
        update_data['hashed_password'] = get_password_hash(password)

    stored_user_model = await get_user(db, username)
    updated_user = stored_user_model.model_copy(update=update_data)

    await update_user(db, current_user.username, updated_user.username, updated_user.model_dump_json())

    return updated_user


@router.get('/', response_model=list[User])
async def get_users(
        current_user: Annotated[User, Depends(get_current_active_user)],
        db: Annotated[Redis, Depends(get_db)],
):
    response = [await get_user(db, username) async for username in db.scan_iter()]
    return response


@router.post("/", response_model=User)
async def insert_user(
        current_user: Annotated[User, Depends(get_current_active_user)],
        new_user: UserInCreate,
        db: Annotated[Redis, Depends(get_db)],
):
    if not current_user.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Requires admin privileges')

    user = await get_user(db, new_user.username)
    if user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User already exists')

    user_dict = new_user.model_dump()
    hashed_password = get_password_hash(user_dict.pop('password'))
    user_model = UserInDB(**user_dict, hashed_password=hashed_password)

    await create_user(db, user_model.username, user_model.model_dump_json())

    return user_model


@router.delete('/{username}', status_code=status.HTTP_204_NO_CONTENT)
async def remove_user(
        current_user: Annotated[User, Depends(get_current_active_user)],
        username: str,
        db: Annotated[Redis, Depends(get_db)],
):
    if username == 'me':
        username = current_user.username
    elif username != current_user.username and not current_user.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Requires admin privileges')

    await delete_user(db, username)
