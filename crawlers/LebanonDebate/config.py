from datetime import date
import os

# Target website name
CRAWLER_NAME = "Lebanon Debate"

# Website IP for media sending via API
HOST_URL = "http://127.0.0.1:5000"

# URLs for desired pages to scrape
TARGETS_PAGE_URL = [
    f"https://www.lebanondebate.com/category/211-%D8%A7%D9%84%D8%A3%D8%AE%D8%A8%D8%A7%D8%B1-%D8%A7%D9%84%D9%85%D9%87%D9%85%D8%A9",
    # f"https://www.lebanondebate.com/category/139-%D8%B1%D8%A7%D8%AF%D8%A7%D8%B1",
    # f"https://www.lebanondebate.com/category/206-%D8%A8%D8%AD%D8%AB-%D9%88%D8%AA%D8%AD%D8%B1%D9%8A",
    # f"https://www.lebanondebate.com/category/134-%D8%A7%D9%84%D9%85%D8%AD%D9%84%D9%8A%D8%A9",
    # f"https://www.lebanondebate.com/category/178-%D8%A3%D9%85%D9%86-%D9%88%D9%82%D8%B6%D8%A7%D8%A1",
    # f"https://www.lebanondebate.com/category/142-%D8%A7%D9%82%D9%84%D9%8A%D9%85%D9%8A-%D9%88%D8%AF%D9%88%D9%84%D9%8A",
]

# Cache for the articles ID path (by SQLite)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # current folder (crawler folder)
DB_FOLDER = os.path.join(BASE_DIR, "db")
os.makedirs(DB_FOLDER, exist_ok=True)
SQLite_DB_PATH = os.path.join(DB_FOLDER, "cache.db")


# Databse URL
DB_URL = "mysql+pymysql://neptune_user:neptunized128@localhost/neptune"
