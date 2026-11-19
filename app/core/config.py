import os

SECRET_KEY = os.getenv("SECRET_KEY", "ctech-inventory-secret-key-2024-cao-hoc")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12  # 12 hours
