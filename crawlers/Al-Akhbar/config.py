import os

# Cache for the articles ID path (by SQLite)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # current folder (crawler folder)
DB_FOLDER = os.path.join(BASE_DIR, "db")
os.makedirs(DB_FOLDER, exist_ok=True)
SQLite_DB_PATH = os.path.join(DB_FOLDER, "cache.db")


# Databse URL
DB_URL = "mysql+pymysql://neptune_user:neptunized128@localhost/neptune"
