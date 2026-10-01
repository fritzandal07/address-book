import os

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./address_book.db")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
