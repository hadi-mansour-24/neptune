from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from models import Article, Crawler, CrawlerLog
from selenium.webdriver.common.by import By
from config import SQLite_DB_PATH
from selenium import webdriver
from bs4 import BeautifulSoup
from datetime import datetime
import sqlite3
import random
import time


class AlAkhbar:
    def __init__(self):
        self.name = "Al-Akhbar"
        self.home_page = "https://al-akhbar.com"
        self.pages = [
            "https://www.al-akhbar.com/category/lebanon/",
            "https://www.al-akhbar.com/category/palestine",
            "https://www.al-akhbar.com/category/syria",
            "https://www.al-akhbar.com/category/arab-world",
        ]
        self.links = []
        self.create_cache_table()
        self.scraped_articles = 0
        self.driver = self.start_driver()
        self.crawler_id = Crawler.get_crawler_id(crawler_name=self.name)
        Crawler.update_crawler_last_seen(crawler_name=self.name)

    def create_cache_table(self):
        try:
            conn = sqlite3.connect(SQLite_DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS article_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_id TEXT UNIQUE
                )
            """
            )
            conn.commit()
            conn.close()
        except Exception as e:
            CrawlerLog.add_log(
                crawler_id=self.crawler_id,
                log_level="URGENT",
                message=f"Failed creating cache table: {e}",
            )

    def check_article_existance(self, article_id):
        """
        This method checks if an article ID exists in the cache.
        Returns True if it exists, False otherwise.
        Insert tge id in case it does not exist.
        """
        try:
            conn = sqlite3.connect(SQLite_DB_PATH)
            cursor = conn.cursor()

            # Check if the article_id exists
            cursor.execute(
                "SELECT id FROM article_cache WHERE entry_id = ?", (article_id,)
            )
            result = cursor.fetchone()

            if result:
                # Article already cached
                conn.close()
                return True
            else:
                # Insert the new id to cache
                cursor.execute(
                    "INSERT INTO article_cache (entry_id) VALUES (?)", (article_id,)
                )
                conn.commit()
                conn.close()
                return False

        except Exception as e:
            CrawlerLog.add_log(
                crawler_id=self.crawler_id,
                log_level="WARNING",
                message=f"Caching failed for {article_id}: {e}",
            )
            return False

    def start_driver(self):
        """
        Initialize and configure a Selenium WebDriver with Chrome browser
        Returns: WebDriver instance with configured options
        """

        # Create Chrome options to customize browser behavior
        chrome_options = Options()

        # Add argument to run browser in headless mode (without GUI)
        chrome_options.add_argument("--headless=new")

        # Add argument to disable popup blocking
        chrome_options.add_argument("--disable-popup-blocking")

        # Options to mute the logs
        chrome_options.add_argument("--log-level=3")  # Only show fatal errors
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        chrome_options.add_argument("--disable-logging")

        # Initialize the Chrome driver service with automatic driver management
        # ChromeDriverManager automatically downloads and manages the correct driver version
        service = Service(ChromeDriverManager().install())

        # Create the WebDriver instance with configured options and service
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Set implicit wait to automatically wait for elements to appear
        # This applies to all find_element operations (default wait: 10 seconds)
        driver.implicitly_wait(10)

        return driver

    def download_article_links(self):
        for page in self.pages:
            self.driver.get(page)
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(random.randint(10, 20))
            html_content = self.driver.page_source
            soup = BeautifulSoup(html_content, "html.parser")
            articles_links = soup.find_all("a", class_="mb-2 max-md:mb-0")
            time.sleep(random.randint(5, 32))
            for link in articles_links:
                article_url = link.get("href")
                if article_url:
                    self.links.append(self.home_page + article_url)

    def download_articles(self):
        for link in self.links:
            self.driver.get(link)
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(random.randint(10, 20))
            html_content = self.driver.page_source
            soup = BeautifulSoup(html_content, "html.parser")
            article_id = next(part for part in link.split("/") if part.isdigit())
            article_id = "AKHBAR-" + article_id
            # Check if the article already exists in the cache
            if self.check_article_existance(article_id):
                continue
            # Extract article details
            # Title
            title_tag = soup.find(
                "h1", class_="title text-4xl lg:text-5xl"
            ).text.strip()

            # Content
            content_div = soup.find("div", class_="post-details-content")
            if content_div:
                full_content = ""
                child_content_div = content_div.find("div", class_="w-full")
                for paragraph in child_content_div.find_all("p"):
                    full_content += paragraph.text.strip() + "\n"
                    # Get the publish date
                    publish_date = arabic_date_to_datetime(
                        soup.find("div", class_="mt-1 flex").text.strip()
                    )

            try:
                # Save article to the database
                Article.add_article(
                    crawler_id=self.crawler_id,
                    entry_id=article_id,
                    title=title_tag,
                    content=full_content,
                    article_url=link,
                    has_media=False,
                    publish_date=publish_date,
                )
                self.scraped_articles += 1
            except Exception as e:
                CrawlerLog.add_log(
                    crawler_id=self.crawler_id,
                    log_level="URGENT",
                    message=f"{e}",
                )


def arabic_date_to_datetime(date_str, hour=0, minute=0, second=0):
    months = {
        "كانون الثاني": 1,
        "شباط": 2,
        "آذار": 3,
        "نيسان": 4,
        "أيار": 5,
        "حزيران": 6,
        "تموز": 7,
        "آب": 8,
        "أيلول": 9,
        "تشرين الأول": 10,
        "تشرين الثاني": 11,
        "كانون الأول": 12,
    }

    parts = date_str.split()
    day = int(parts[1])
    month = months[parts[2]]
    year = int(parts[3])

    dt = datetime(year, month, day, hour, minute, second)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    al_akhbar = AlAkhbar()
    al_akhbar.download_article_links()
    al_akhbar.download_articles()
    CrawlerLog.add_log(
        crawler_id=al_akhbar.crawler_id,
        log_level="INFO",
        message=f"Scraping Done.. Scraped {al_akhbar.scraped_articles} articles.",
    )
    time.sleep(5)
    al_akhbar.driver.quit()
