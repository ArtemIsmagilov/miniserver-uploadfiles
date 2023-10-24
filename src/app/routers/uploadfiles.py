from typing import Annotated
import os, csv, aiofiles, pandas as pd
from aiofiles import os as aiofiles_os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query

from ..constants import PATH_FILES
from ..dependencies import get_current_active_user
from ..schemas.users import User

router = APIRouter(
    prefix='/uploadfiles',
    tags=['uploadfiles'],
)


@router.post("/")
async def create_uploadfiles(
        current_user: Annotated[User, Depends(get_current_active_user)],
        files: Annotated[list[UploadFile], File(description="Multiple files as UploadFile", max_length=1048576)],
):
    fileinfos = []
    listdir = await aiofiles_os.listdir(os.path.join(PATH_FILES, current_user.username))
    for indx, upfile in enumerate(files):

        if upfile.filename in listdir:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File already exists")
        else:
            fileinfos.append({'filename': upfile.filename, 'size': upfile.size})

        context = await upfile.read()

        path_to_file = os.path.join(PATH_FILES, current_user.username, upfile.filename)
        async with aiofiles.open(path_to_file, mode='wb') as outfile:
            await outfile.write(context)

    return {"fileinfos": fileinfos}


@router.get("/")
async def read_uploadfiles(
        current_user: Annotated[User, Depends(get_current_active_user)],
):
    response = {}
    a = os.path.join(PATH_FILES, current_user.username)
    listdir = await aiofiles_os.listdir(os.path.join(PATH_FILES, current_user.username))

    for filename in listdir:
        path_to_file_in = os.path.join(PATH_FILES, current_user.username, filename)
        async with aiofiles.open(path_to_file_in, encoding='utf-8') as csv_file:
            line = await csv_file.readline()
        if not line:
            fieldnames = []
        else:
            fieldnames = next(csv.reader((line,)))

        response[filename] = {'fieldnames': fieldnames}

    return response


@router.get("/{filename}")
async def read_uploadfile(
        current_user: Annotated[User, Depends(get_current_active_user)],
        filename: str,
        headers: str | None = None,
        sort_by: str | None = None,
):
    filenames = await aiofiles_os.listdir(os.path.join(PATH_FILES, current_user.username))
    if filename not in filenames:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filename not found")

    df = pd.read_csv(os.path.join(PATH_FILES, current_user.username, filename))

    if headers:
        try:
            df = df[headers.split(',')]
        except KeyError as exp:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad param headers")

    if sort_by:
        try:
            df = df.sort_values(by=sort_by.split(','))
        except KeyError as exp:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad param sort_by")

    return {'csv_table': df.head(3).to_csv(index=False, encoding='utf-8')}


@router.delete("/{filename}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_uploadfile(
        current_user: Annotated[User, Depends(get_current_active_user)],
        filename: str,
):
    path_file = os.path.join(PATH_FILES, current_user.username, filename)
    isfile = await aiofiles_os.path.isfile(path_file)
    if not isfile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filename not found")

    await aiofiles_os.remove(path_file)
