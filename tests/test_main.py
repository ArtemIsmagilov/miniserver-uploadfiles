import pytest, asyncio
from httpx import AsyncClient
from datetime import timedelta
from redis.asyncio import Redis
from fastapi import status

from src.app.constants import APP_URL, BASE_DIR
from tests.conftest import test_admin_user, test_client_user, files, get_headers_dict
from src.app.dependencies import create_access_token, get_db
from src.app.sql_app.crud import get_user
from src.app.main import app


class TestPre:

    @pytest.mark.asyncio
    async def test_users_exists(self, u1=test_admin_user, u2=test_client_user):
        db: Redis = await anext(get_db())

        assert await get_user(db, u1.username)
        assert await get_user(db, u2.username)


class TestAuth:
    endpoint = '/token/'

    @pytest.mark.parametrize(('username', 'password'), (
            (test_admin_user.username, 'wrong password',),
            ('wrong username', test_admin_user.password,),
            (test_client_user.username, 'wrong password',),
            ('wrong username', test_client_user.password,),
    ))
    @pytest.mark.asyncio
    async def test_auth_401(self, username, password):
        data = {'username': username, 'password': password}
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.post(self.endpoint, data=data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(('user',), (
            (test_admin_user,),
            (test_client_user,),
    ))
    @pytest.mark.asyncio
    async def test_auth_200(self, user):
        data = {'username': user.username, 'password': user.password}
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.post(self.endpoint, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['access_token']


class TestUsers:
    endpoint = '/users/'

    # not authorization read user me 401
    @pytest.mark.parametrize(('user', 'headers'), (
            (test_admin_user, get_headers_dict()),
            (test_client_user, get_headers_dict(
                create_access_token(data={"sub": test_admin_user.username}, expires_delta=timedelta(microseconds=1))
            )
             )
            ,
    ))
    @pytest.mark.asyncio
    async def test_read_user_me_401(self, user, headers):
        await asyncio.sleep(1)
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.get(self.endpoint + 'me', headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # success read user me 200
    @pytest.mark.parametrize(('user',), (
            (test_admin_user,),
            (test_client_user,),
    ))
    @pytest.mark.asyncio
    async def test_read_user_me_200(self, user):
        headers = get_headers_dict(user.token)
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.get(self.endpoint + 'me', headers=headers)

        assert response.status_code == status.HTTP_200_OK

    # invalid Body put user 401
    @pytest.mark.parametrize(('user', 'update_data'), (
            (test_admin_user, {'full_name': 'updated_full_name'}),
            (test_client_user, {'full_name': 'updated_full_name'}),
    ))
    @pytest.mark.asyncio
    async def test_put_user_401(self, user, update_data):
        headers = get_headers_dict()
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.put(self.endpoint + 'me', headers=headers, json=update_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # invalid Body put user 422
    @pytest.mark.parametrize(('user', 'update_data'), (
            (test_admin_user, {'full_name': 67126717828}),
            (test_client_user, {'email': 'sad'}),
    ))
    @pytest.mark.asyncio
    async def test_put_user_invalid(self, user, update_data):
        headers = get_headers_dict(user.token)
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.put(self.endpoint + 'me', headers=headers, json=update_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # success put user me 200
    @pytest.mark.parametrize(('user', 'update_data'), (
            (test_admin_user, {'full_name': 'updated_full_name'}),
            (test_client_user, {'full_name': 'updated_full_name'}),
    ))
    @pytest.mark.asyncio
    async def test_put_user_me_200(self, user, update_data):
        headers = get_headers_dict(user.token)
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.put(self.endpoint + 'me', headers=headers, json=update_data)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['full_name'] == update_data['full_name']

    # success put other user 200
    @pytest.mark.parametrize(('user', 'update_data'), (
            (test_admin_user, {'full_name': 'updated_full_name'}),
    ))
    @pytest.mark.asyncio
    async def test_put_admin_user_200(self, user, update_data):
        headers = get_headers_dict(user.token)
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.put(self.endpoint + 'admin', headers=headers, json=update_data)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['full_name'] == update_data['full_name']

    # no admin privileges for put other user 403
    @pytest.mark.parametrize(('user', 'update_data'), (
            (test_client_user, {'full_name': 'updated_full_name'}),
    ))
    @pytest.mark.asyncio
    async def test_put_client_user_403(self, user, update_data):
        headers = get_headers_dict(user.token)
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.put(self.endpoint + 'admin', headers=headers, json=update_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    # success get users 200
    @pytest.mark.parametrize(('user',), (
            (test_admin_user,),
            (test_client_user,),
    ))
    @pytest.mark.asyncio
    async def test_get_users_200(self, user):
        headers = get_headers_dict(user.token)
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.get(self.endpoint, headers=headers)

        assert response.status_code == status.HTTP_200_OK

    # no auth get users 401
    @pytest.mark.parametrize(('user',), (
            (test_admin_user,),
            (test_client_user,),
    ))
    @pytest.mark.asyncio
    async def test_get_users_401(self, user):
        headers = get_headers_dict()
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.get(self.endpoint, headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # success admin create user 200
    @pytest.mark.parametrize(('user', 'name', 'mysecret'), (
            (test_admin_user, 'new_username1', 'new_password1'),
            (test_admin_user, 'new_username2', 'new_password2'),
    ))
    @pytest.mark.asyncio
    async def test_create_admin_user_200(self, user, name, mysecret):
        headers = get_headers_dict(user.token)
        data = {'username': name, 'password': mysecret}
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.post(self.endpoint, headers=headers, json=data)
        assert response.status_code == status.HTTP_200_OK

    # bad admin create user 400
    @pytest.mark.parametrize(('user',), (
            (test_admin_user,),
    ))
    @pytest.mark.asyncio
    async def test_admin_create_user_400(self, user):
        headers = get_headers_dict(user.token)
        data = {'username': test_client_user.username, 'password': test_client_user.password}
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.post(self.endpoint, headers=headers, json=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # invalid admin create user 422
    @pytest.mark.parametrize(('user', 'data'), (
            (test_admin_user, {'username': 8818, 'password': 'new_password'}),
            (test_admin_user, {'password': 'new_password'}),
            (test_admin_user, {'username': '8818', 'email': 'sad'}),
    ))
    @pytest.mark.asyncio
    async def test_create_user_422(self, user, data):
        headers = get_headers_dict(user.token)
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.post(self.endpoint, headers=headers, json=data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # no auth admin create user 401
    @pytest.mark.parametrize(('user',), (
            (test_admin_user,),
    ))
    @pytest.mark.asyncio
    async def test_create_user_401(self, user):
        headers = get_headers_dict()
        data = {'username': 'new_username', 'password': 'new_password'}
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.post(self.endpoint, headers=headers, json=data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # success admin delete user 204
    @pytest.mark.parametrize(('other_username',), (
            ('new_username1',),
            ('new_username2',),
    ))
    @pytest.mark.asyncio
    async def test_delete_admin_other_user_204(self, other_username):
        headers = get_headers_dict(test_admin_user.token)
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.delete(self.endpoint + other_username, headers=headers)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    # no delete admin delete user 400
    @pytest.mark.parametrize(('user', 'other_username'), (
            (test_admin_user, 'kjajsjlkfslkflkjskllkmlkavmc,v,mxc'),
    ))
    @pytest.mark.asyncio
    async def test_delete_admin_other_user_400(self, user, other_username):
        headers = get_headers_dict(user.token)
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.delete(self.endpoint + other_username, headers=headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # no client delete other user 403
    @pytest.mark.parametrize(('user', 'other_username'), (
            (test_client_user, 'new_username2'),
    ))
    @pytest.mark.asyncio
    async def test_delete_client_other_user_403(self, user, other_username):
        headers = get_headers_dict(user.token)
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.delete(self.endpoint + other_username, headers=headers)
            # admin have privileges
            await ac.delete(self.endpoint + other_username,
                            headers={'Authorization': 'Bearer ' + test_admin_user.token})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    # no auth delete other user 401
    @pytest.mark.parametrize(('user', 'other_username'), (
            (test_admin_user, 'me'),
            (test_client_user, 'me'),
    ))
    @pytest.mark.asyncio
    async def test_delete_admin_other_user_401(self, user, other_username):
        headers = get_headers_dict()
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.delete(self.endpoint + other_username, headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUploadFiles:
    endpoint = '/uploadfiles/'

    # user success upload files 200
    @pytest.mark.parametrize(('user',), (
            (test_admin_user,),
            (test_client_user,),
    ))
    @pytest.mark.asyncio
    async def test_create_uploadfiles_200(self, user):
        headers = get_headers_dict(user.token)
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.post(self.endpoint, headers=headers, files=files)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['fileinfos'][0]['filename'] == 'organizations.csv'
        assert data['fileinfos'][1]['filename'] == 'people.csv'

    # no auth user upload files 401
    @pytest.mark.asyncio
    async def test_create_uploadfiles_401(self):
        headers = get_headers_dict()
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.post(self.endpoint, headers=headers, files=files)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # success read user's upload files
    @pytest.mark.parametrize(('user',), (
            (test_admin_user,),
            (test_client_user,),
    ))
    @pytest.mark.asyncio
    async def test_read_uploadfiles_200(self, user):
        headers = {'Authorization': 'Bearer ' + user.token}
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.get(self.endpoint, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['people.csv'][
                   'fieldnames'] == 'Index,User Id,First Name,Last Name,Sex,Email,Phone,Date of birth,Job Title'.split(
            ',')
        assert data['organizations.csv'][
                   'fieldnames'] == 'Index,Organization Id,Name,Website,Country,Description,Founded,Industry,Number of employees'.split(
            ',')

    # success read user's upload file by filename
    @pytest.mark.parametrize(('user',), (
            (test_admin_user,),
            (test_client_user,),
    ))
    @pytest.mark.asyncio
    async def test_read_file_200(self, user):
        headers = get_headers_dict(user.token)
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.get(self.endpoint + 'people.csv', headers=headers)

        assert response.status_code == status.HTTP_200_OK

    # success read user's upload file by filename
    @pytest.mark.parametrize(('user', 'params'), (
            (test_admin_user, {'headers': 'Index,Organization Id', 'sort_by': 'Organization Id'}),
            (test_client_user, {'headers': 'Description,Founded,Industry,Number of employees'}),
            (test_client_user, {}),
    ))
    @pytest.mark.asyncio
    async def test_read_file_with_query_200(self, user, params):
        headers = get_headers_dict(user.token)
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.get(self.endpoint + 'organizations.csv', headers=headers, params=params)

        assert response.status_code == status.HTTP_200_OK

    # invalid quary read user's upload file by filename
    @pytest.mark.parametrize(('user', 'params'), (
            (test_admin_user, {'sort_by': 'Organizatsadasion Id,,,./.,/.,/as,d.as,'}),
            (test_client_user, {'headers': 'Description;;;;Founded,s,/.,/./..Industry,Number of employees'}),
    ))
    @pytest.mark.asyncio
    async def test_read_file_with_query_200(self, user, params):
        headers = get_headers_dict(user.token)
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.get(self.endpoint + 'organizations.csv', headers=headers, params=params)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # read user's upload file by filename 404
    @pytest.mark.parametrize(('user',), (
            (test_admin_user,),
            (test_client_user,),
    ))
    @pytest.mark.asyncio
    async def test_read_file_404(self, user):
        headers = get_headers_dict(user.token)
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.get(self.endpoint + 'unknow.csv', headers=headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # no auth read user's upload file by filename 401
    @pytest.mark.asyncio
    async def test_read_file_401(self):
        headers = get_headers_dict()
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.get(self.endpoint + 'unknow.csv', headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # no auth delete user's upload file by filename 401
    @pytest.mark.asyncio
    async def test_delete_file_401(self):
        headers = get_headers_dict()
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.delete(self.endpoint + 'people.csv', headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # no delete user's upload file by filename 404
    @pytest.mark.parametrize(('user',), (
            (test_admin_user,),
            (test_client_user,),
    ))
    @pytest.mark.asyncio
    async def test_delete_file_404(self, user):
        headers = get_headers_dict(user.token)
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.delete(self.endpoint + 'known.csv', headers=headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # success delete user's upload file by filename 204
    @pytest.mark.parametrize(('user', 'filename'), (
            (test_admin_user, 'people.csv'),
            (test_client_user, 'organizations.csv'),
    ))
    @pytest.mark.asyncio
    async def test_delete_file_204(self, user, filename):
        headers = get_headers_dict(user.token)
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.delete(self.endpoint + filename, headers=headers)

        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestPosr:

    # success delete users me 204, empty DB
    @pytest.mark.parametrize(('user',), (
            (test_admin_user,),
            (test_client_user,),
    ))
    @pytest.mark.asyncio
    async def test_users_removed(self, user):
        headers = get_headers_dict(user.token)
        async with AsyncClient(app=app, base_url=APP_URL) as ac:
            response = await ac.delete('/users/' + 'me', headers=headers)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        db: Redis = await anext(get_db())

        assert None == await get_user(db, user.username)
