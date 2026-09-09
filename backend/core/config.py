import os

from dotenv import load_dotenv


load_dotenv()

SECRET_KEY = os.environ["SECRET_KEY"]

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://adrijghosh8.github.io",
]
