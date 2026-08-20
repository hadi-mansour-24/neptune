from datetime import date
import os

# Target website name
CRAWLER_NAME = "IMLebanon"

# Website IP for media sending via API
HOST_URL = "http://127.0.0.1:5000"

# URLs for desired pages to scrape
"""Each website has its own structure"""
"""IMLebanon has a structure that displays the articles by date, as following"""
"""The plan is to scrape the posts regarding current day from this month and this year"""

current_date = date.today()
current_year = current_date.year
current_month = current_date.month
current_day = current_date.day

TARGET_PAGE_URL = (
    f"https://www.imlebanon.org/{current_year}/{current_month}/{current_day}/"
)
# TARGET_PAGE_URL = f"https://www.imlebanon.org/2025/12/5/"

# Cache for the articles ID path (by SQLite)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # current folder (crawler folder)
DB_FOLDER = os.path.join(BASE_DIR, "db")
os.makedirs(DB_FOLDER, exist_ok=True)
SQLite_DB_PATH = os.path.join(DB_FOLDER, "cache.db")


# Databse URL
DB_URL = "mysql+pymysql://neptune_user:neptunized128@localhost/neptune"
