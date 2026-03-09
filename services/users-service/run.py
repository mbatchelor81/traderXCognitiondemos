"""Entry point for users-service."""

import uvicorn

from app.config import APP_HOST, APP_PORT
from app.database import create_tables
from app.seed import seed_database

if __name__ == "__main__":
    create_tables()
    seed_database()
    uvicorn.run("app.main:app", host=APP_HOST, port=APP_PORT, reload=False)
