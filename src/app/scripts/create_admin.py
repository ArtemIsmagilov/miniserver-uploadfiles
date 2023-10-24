import getpass, asyncio
from redis.asyncio import Redis

from ..dependencies import get_password_hash, get_db
from ..schemas.users import UserInDB
from ..sql_app.crud import create_user, get_user


async def create_user_admin():
    username = input('Username: ').strip() or None
    email = input('Email: ').strip() or None
    full_name = input('Full name: ').strip() or None
    password = getpass.getpass().strip() or None
    if password:
        hashed_password = get_password_hash(password)
    else:
        hashed_password = None

    admin = UserInDB(username=username, hashed_password=hashed_password, email=email, full_name=full_name, admin=True)
    db: Redis = await anext(get_db())
    user = await get_user(db, admin.username)
    if user:
        print('User already exists')
    else:
        await create_user(db, admin.username, admin.model_dump_json())


async def main():
    await create_user_admin()


if __name__ == '__main__':
    asyncio.run(main())
