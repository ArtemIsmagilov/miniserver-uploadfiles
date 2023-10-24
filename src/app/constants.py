import os, dotenv
from pathlib import Path

dotenv.load_dotenv()

APP_HOST = os.environ['APP_HOST']
APP_PORT = os.environ['APP_PORT']
APP_URL = os.environ['APP_URL']
SECRET_KEY = os.environ['SECRET_KEY']
ALGORITHM = os.environ['ALGORITHM']
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ['ACCESS_TOKEN_EXPIRE_MINUTES'])
REDIS_URL = os.environ['REDIS_URL']
BASE_DIR = Path(__file__).resolve().parent.parent
PATH_FILES = os.path.join(BASE_DIR / 'app', 'files')
