from selenium.webdriver.support import expected_conditions as EC
from config import TARGET_PAGE_URL, CRAWLER_NAME, SQLite_DB_PATH
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from models import Article, Crawler, CrawlerLog
from selenium.webdriver.common.by import By
from urllib.parse import urlparse
from selenium import webdriver
from bs4 import BeautifulSoup
from datetime import datetime
import requests
import sqlite3
import shutil
import os


class IMLebanon:
    def __init__(self):
        self.crawler_id = Crawler.get_crawler_id(crawler_name=CRAWLER_NAME)
        Crawler.update_crawler_last_seen(CRAWLER_NAME)
        self.navigation_links = [TARGET_PAGE_URL]
        self.create_cache_table()
        self.driver = self.start_driver()
        # TEMPORARILY DISABLED: Media/image downloading feature
        # self.downloaded_images = 0
        self.scraped_articles = 0
        self.articles_links = []

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
                log_level="WARNING",
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

    def get_articles_links(self):
        """This function uses the driver to navigate to the target pages"""
        try:
            page_number = 1

            while True:
                # Build URL
                if page_number == 1:
                    page_url = TARGET_PAGE_URL
                else:
                    page_url = TARGET_PAGE_URL + f"page/{page_number}/"

                try:
                    self.driver.get(page_url)
                    WebDriverWait(self.driver, 30).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//body[contains(@class, 'archive date')]")
                        )
                    )
                except:
                    # We reached the last available page, so break
                    break

                html_content = self.driver.page_source
                if not html_content:
                    CrawlerLog.add_log(
                        crawler_id=self.crawler_id,
                        log_level="WARNING",
                        message="No HTML content - stopping",
                    )
                    break

                soup = BeautifulSoup(html_content, "html.parser")
                html_body_tag = soup.find(
                    "body", class_=lambda x: x and "archive date" in x
                )

                # The following is stop condition, to know that the pages ended for this day
                if html_body_tag and "error404" in html_body_tag.get("class", []):
                    break

                # Extract articles
                main_section = (
                    html_body_tag.find("main", class_="main") or html_body_tag
                )
                articles_elements = main_section.find_all(
                    "article", class_=lambda x: x and x.startswith("row post-")
                )

                if articles_elements:
                    # Extract articles
                    page_links_count = 0
                    for article_element in articles_elements:
                        classes = article_element.get("class", [])
                        for cls in classes:
                            if cls.startswith("post-") and cls[5:].isdigit():
                                article_id = f"IML-{cls[5:]}"
                                break  # break from checking the classes, class is found successfully
                        if self.check_article_existance(article_id):
                            continue
                        header = article_element.find("header")
                        if header:
                            h2 = header.find("h2", class_="entry-title")
                            if h2:
                                link_element = h2.find("a", href=True)
                        else:
                            link_element = article_element.find("a", href=True)

                        if link_element:
                            link = link_element["href"]
                            if link not in self.articles_links:
                                self.articles_links.append(link)
                                page_links_count += 1

                page_number += 1

        except Exception as e:
            error_msg = str(e).lower()
            if any(
                phrase in error_msg
                for phrase in [
                    "net::",
                    "connection",
                    "timeout",
                    "unreachable",
                    "refused",
                    "reset",
                    "failed",
                    "disconnected",
                ]
            ):
                CrawlerLog.add_log(
                    crawler_id=self.crawler_id,
                    log_level="ERROR",
                    message="INTERNET CONNECTION ERROR - Please check your connection",
                )
                return self.articles_links
            else:
                CrawlerLog.add_log(
                    crawler_id=self.crawler_id,
                    log_level="WARNING",
                    message=f"Could not load page {page_number} - stopping: {e}",
                )

    # def get_articles_links(self):
    #     """This function uses the driver to navigate to target daily pages (1-30)"""
    #     try:
    #         # Iterate over days 1 to 30
    #         for day in range(16, 31):
    #             page_number = 1

    #             while True:
    #                 # Build URL: e.g., https://www.imlebanon.org/2025/12/5/page/2/
    #                 if page_number == 1:
    #                     page_url = f"https://www.imlebanon.org/2025/12/{day}/"
    #                 else:
    #                     page_url = f"https://www.imlebanon.org/2025/12/{day}/page/{page_number}/"

    #                 try:
    #                     self.driver.get(page_url)
    #                     WebDriverWait(self.driver, 30).until(
    #                         EC.presence_of_element_located(
    #                             (By.XPATH, "//body[contains(@class, 'archive date')]")
    #                         )
    #                     )
    #                 except:
    #                     # No more pages for this day
    #                     break

    #                 html_content = self.driver.page_source
    #                 if not html_content:
    #                     CrawlerLog.add_log(
    #                         crawler_id=self.crawler_id,
    #                         log_level="WARNING",
    #                         message=f"No HTML content for day {day} - stopping",
    #                     )
    #                     break

    #                 soup = BeautifulSoup(html_content, "html.parser")
    #                 html_body_tag = soup.find(
    #                     "body", class_=lambda x: x and "archive date" in x
    #                 )

    #                 if html_body_tag and "error404" in html_body_tag.get("class", []):
    #                     # No articles for this day
    #                     break

    #                 # Extract articles
    #                 main_section = (
    #                     html_body_tag.find("main", class_="main") or html_body_tag
    #                 )
    #                 articles_elements = main_section.find_all(
    #                     "article", class_=lambda x: x and x.startswith("row post-")
    #                 )

    #                 if articles_elements:
    #                     page_links_count = 0
    #                     for article_element in articles_elements:
    #                         classes = article_element.get("class", [])
    #                         article_id = None
    #                         for cls in classes:
    #                             if cls.startswith("post-") and cls[5:].isdigit():
    #                                 article_id = f"IML-{cls[5:]}"
    #                                 break
    #                         if not article_id or self.check_article_existance(
    #                             article_id
    #                         ):
    #                             continue

    #                         header = article_element.find("header")
    #                         if header:
    #                             h2 = header.find("h2", class_="entry-title")
    #                             if h2:
    #                                 link_element = h2.find("a", href=True)
    #                             else:
    #                                 link_element = None
    #                         else:
    #                             link_element = article_element.find("a", href=True)

    #                         if link_element:
    #                             link = link_element["href"]
    #                             if link not in self.articles_links:
    #                                 self.articles_links.append(link)
    #                                 page_links_count += 1

    #                 page_number += 1

    #     except Exception as e:
    #         error_msg = str(e).lower()
    #         if any(
    #             phrase in error_msg
    #             for phrase in [
    #                 "net::",
    #                 "connection",
    #                 "timeout",
    #                 "unreachable",
    #                 "refused",
    #                 "reset",
    #                 "failed",
    #                 "disconnected",
    #             ]
    #         ):
    #             CrawlerLog.add_log(
    #                 crawler_id=self.crawler_id,
    #                 log_level="WARNING",
    #                 message="INTERNET CONNECTION ERROR - Please check your connection",
    #             )
    #             return self.articles_links
    #         else:
    #             CrawlerLog.add_log(
    #                 crawler_id=self.crawler_id,
    #                 log_level="WARNING",
    #                 message=f"Could not load page - stopping: {e}",
    #             )

    #     return self.articles_links

    def download_articles_data(self):
        for article_link in self.articles_links:
            self.driver.get(article_link)
            try:
                # Get page source then main section
                html_content = self.driver.page_source
                soup = BeautifulSoup(html_content, "html.parser")
                main_section = soup.find("main", class_="main")

                article_element = main_section.find(
                    "article", class_=lambda x: x and x.startswith("post-")
                )

                article_id = ""
                if article_element:
                    classes = article_element.get("class", [])
                    for cls in classes:
                        if cls.startswith("post-") and cls[5:].isdigit():
                            article_id = f"IML-{cls[5:]}"
                            break  # break from checking the classes, class is found successfully

                # Download the article title
                article_title = main_section.find("h1", class_="entry-title").text
                article_content_element = main_section.find(
                    "div", class_="entry-content"
                )

                # Download article content (text)
                article_content = ""
                if article_content_element:
                    text_paragraphs = article_content_element.find_all("p")
                    for text_paragraph in text_paragraphs:
                        article_content += text_paragraph.text

                article_post_date = main_section.find("time", class_="updated").text

                try:
                    publish_date = datetime.strptime(
                        article_post_date, "%B %d, %Y %I:%M %p"
                    )
                except ValueError as e:
                    CrawlerLog.add_log(
                        crawler_id=self.crawler_id,
                        log_level="WARNING",
                        message=f"Failed to parse date '{article_post_date}': {e}",
                    )
                    publish_date = None

                # TEMPORARILY DISABLED: Download images links and send via API
                # has_media = 0
                # if article_element:
                #     image_element = article_element.find("img")
                #     if image_element:
                #         image_link = image_element.get("src")
                #         has_media = self.download_image(
                #             image_url=image_link, article_id=article_id
                #         )
                #         if has_media:
                #             tmp_folder = os.path.join(
                #                 os.path.dirname(os.path.abspath(__file__)),
                #                 "tmp",
                #                 article_id,
                #             )
                #             if os.path.exists(tmp_folder):
                #                 for filename in os.listdir(tmp_folder):
                #                     file_path = os.path.join(tmp_folder, filename)
                #                     with open(file_path, "rb") as f:
                #                         # Send each image scraped to the server
                #                         # the url will change when the website is ready for production
                #                         r = requests.post(
                #                             f"http://127.0.0.1:5000/upload_media/{article_id}",
                #                             files={"file": f},
                #                             timeout=10,
                #                         )
                #
                #                         if r.status_code == 200:
                #                             self.downloaded_images += 1
                # TEMPORARILY DISABLED: set has_media to 0 for text content only
                has_media = 0

            except Exception as e:
                error_msg = str(e).lower()
                if any(
                    phrase in error_msg
                    for phrase in [
                        "net::",
                        "connection",
                        "timeout",
                        "unreachable",
                        "refused",
                        "reset",
                        "failed",
                        "disconnected",
                    ]
                ):
                    CrawlerLog.add_log(
                        crawler_id=self.crawler_id,
                        log_level="WARNING",
                        message="INTERNET CONNECTION ERROR - Please check your connection",
                    )
                    return
                else:
                    break

            # insert the data scraped to the database
            # using the methods in the models.py file
            try:
                Article.add_article(
                    crawler_id=self.crawler_id,
                    title=article_title,
                    entry_id=article_id,
                    content=article_content,
                    article_url=article_link,
                    has_media=has_media,
                    publish_date=publish_date,
                )
                self.scraped_articles += 1
            except Exception as e:
                CrawlerLog.add_log(
                    crawler_id=self.crawler_id, log_level="WARNING", message=str(e)
                )

    # TEMPORARILY DISABLED: Image downloading method not needed for text-only content
    # def download_image(self, image_url, article_id):
    #     try:
    #         # Get folder where this script is
    #         base_dir = os.path.dirname(os.path.abspath(__file__))
    #         tmp_folder = os.path.join(base_dir, "tmp")
    #         os.makedirs(tmp_folder, exist_ok=True)
    #
    #         # Folder structure: tmp/IML-post_id/image.extension
    #         article_folder = os.path.join(tmp_folder, f"{article_id}")
    #         os.makedirs(article_folder, exist_ok=True)
    #
    #         # Get the image filename from URL
    #         basename = os.path.basename(urlparse(image_url).path)
    #         save_path = os.path.join(article_folder, basename)
    #
    #         # Download image
    #         r = requests.get(image_url, timeout=10)
    #         r.raise_for_status()
    #         with open(save_path, "wb") as f:
    #             f.write(r.content)
    #
    #         return True
    #
    #     except Exception as e:
    #         print(f"Failed downloading {image_url}: {e}")
    #         return False


if __name__ == "__main__":
    crawler = IMLebanon()
    try:
        crawler.get_articles_links()
        crawler.download_articles_data()
        CrawlerLog.add_log(
            crawler_id=crawler.crawler_id,
            log_level="INFO",
            message=f"Articles Downloaded: {crawler.scraped_articles}",
            # TEMPORARILY DISABLED: Images Downloaded count - media feature disabled
            # message=f"Articles Downloaded: {crawler.scraped_articles} Images Downloaded: {crawler.downloaded_images }",
        )
        # TEMPORARILY DISABLED: Temporary folder cleanup for image downloads
        # base_dir = os.path.dirname(os.path.abspath(__file__))
        # tmp_folder = os.path.join(base_dir, "tmp")
        # if os.path.exists(tmp_folder):
        #     shutil.rmtree(tmp_folder)
    finally:
        crawler.driver.quit()
