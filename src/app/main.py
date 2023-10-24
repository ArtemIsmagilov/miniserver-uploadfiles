from fastapi import FastAPI

from .routers import users, uploadfiles, token

app = FastAPI()
app.include_router(token.router)
app.include_router(users.router)
app.include_router(uploadfiles.router)

# if __name__ == "__main__":
#     import uvicorn
#     from src.app.constants import APP_HOST, APP_PORT
#
#     uvicorn.run(app, host=APP_HOST, port=APP_PORT)
