from config import TARGETS_PAGE_URL, CRAWLER_NAME, SQLite_DB_PATH
from models import Article, Crawler, CrawlerLog
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import requests
import sqlite3
import random
import time

class LDebate:
    def __init__(self):
        self.crawler_id = Crawler.get_crawler_id(crawler_name=CRAWLER_NAME)
        Crawler.update_crawler_last_seen(CRAWLER_NAME)
        self.articles_links = []
        self.create_cache_table()
        # TEMPORARILY DISABLED: Media/image downloading feature
        # self.downloaded_images = 0
        self.scraped_articles = 0

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

    def download_articles_links(self):
        for base_url in TARGETS_PAGE_URL:
            for i in range(11):
                url = f"{base_url}?page={i}"
                response = requests.get(url=url)
                time.sleep(random.randint(0, 10))
                if response.status_code == 200:
                    html_response = response.text
                    soup = BeautifulSoup(html_response, "html.parser")
                    articles_grid = soup.find("div", class_="articles-grid")
                    if articles_grid:
                        anchors = articles_grid.find_all("a", class_="grid-item")
                        for anchor in anchors:
                            link = anchor.get("href")
                            self.articles_links.append(link)
                else:
                    CrawlerLog.add_log(
                        crawler_id=self.crawler_id,
                        log_level="WARNING",
                        message=response.text,
                    )

    def download_articles(self):
        for article_link in self.articles_links:
            response = requests.get(url=article_link)
            if response.status_code == 200:
                html_response = response.text
                if html_response:
                    # Get the entry ID of the article
                    # Split by '/' and take the last part, then split by '-'
                    article_id = article_link.split("/")[-1].split("-")[0]
                    if self.check_article_existance(f"LD-{article_id}"):
                        continue
                    # Parse the html response to the beautifulsoup library
                    # to extract the data from the html
                    soup = BeautifulSoup(html_response, "html.parser")
                    article_page_container = soup.find(
                        "div", class_="article-page-container"
                    )
                    if article_page_container:
                        article_title = article_page_container.find("h1").text
                        article_content = article_page_container.find(
                            "div", class_="article-texts text"
                        )
                        # Get all text from the entire div
                        all_text = article_content.get_text(strip=True, separator=" ")

                        # Get the publish date of the article
                        article_date = self.format_article_date(soup)

                        # TEMPORARILY DISABLED: Download images links and send via API
                        # has_media = 0
                        # image_element = article_page_container.find(
                        #     "img", class_="article-image"
                        # )
                        # if image_element:
                        #     image_link = image_element.get("src")
                        #     has_media = self.download_image(
                        #         image_url=image_link, article_id=article_id
                        #     )
                        #     if has_media:
                        #         tmp_folder = os.path.join(
                        #             os.path.dirname(os.path.abspath(__file__)),
                        #             "tmp",
                        #             f"LD-{article_id}",
                        #         )
                        #         if os.path.exists(tmp_folder):
                        #             for filename in os.listdir(tmp_folder):
                        #                 file_path = os.path.join(tmp_folder, filename)
                        #                 with open(file_path, "rb") as f:
                        #                     # Send each image scraped to the server
                        #                     # the url will change when the website is ready for production
                        #                     r = requests.post(
                        #                         f"http://127.0.0.1:5000/upload_media/LD-{article_id}",
                        #                         files={"file": f},
                        #                         timeout=10,
                        #                     )
                        #
                        #                     if r.status_code == 200:
                        #                         self.downloaded_images += 1
                        # TEMPORARILY DISABLED: set has_media to 0 for text content only
                        has_media = 0
                        try:
                            Article.add_article(
                                crawler_id=self.crawler_id,
                                article_url=article_link,
                                content=all_text,
                                has_media=has_media,
                                title=article_title,
                                entry_id=f"LD-{article_id}",
                                publish_date=article_date,
                            )
                            self.scraped_articles += 1
                        except Exception as e:
                            CrawlerLog.add_log(
                                crawler_id=self.crawler_id,
                                log_level="WARNING",
                                message=str(e),
                            )
                else:
                    CrawlerLog.add_log(
                        crawler_id=self.crawler_id,
                        log_level="WARNING",
                        message="HTML response not found",
                    )

            time.sleep(random.randint(10, 25))

    # TEMPORARILY DISABLED: Image downloading method not needed for text-only content
    # def download_image(self, image_url, article_id):
    #     try:
    #         # Get folder where this script is
    #         base_dir = os.path.dirname(os.path.abspath(__file__))
    #         tmp_folder = os.path.join(base_dir, "tmp")
    #         os.makedirs(tmp_folder, exist_ok=True)
    #
    #         # Folder structure: tmp/LD-post_id/image.extension
    #         article_folder = os.path.join(tmp_folder, f"LD-{article_id}")
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

    def format_article_date(self, soup):
        date_span = soup.find("span", class_="article-date")
        if not date_span:
            return None

        date_text = date_span.get_text(strip=True)

        try:
            # Simple split approach
            parts = date_text.split()

            # Extract components (skip Arabic day name at index 0)
            # Format: [الأحد, 28, كانون, الأول, 2025, -, 16:29]
            if len(parts) >= 7:
                day = int(parts[1])

                # Check if month is two words
                if parts[2] == "كانون" and parts[3] in ["الأول", "الثاني"]:
                    month_name = f"{parts[2]} {parts[3]}"
                    year = int(parts[4])
                    time_str = parts[6]
                elif parts[2] == "تشرين" and parts[3] in ["الأول", "الثاني"]:
                    month_name = f"{parts[2]} {parts[3]}"
                    year = int(parts[4])
                    time_str = parts[6]
                else:
                    # Single word month
                    month_name = parts[2]
                    year = int(parts[3])
                    time_str = parts[5]

                # Parse time
                hour, minute = map(int, time_str.split(":"))

                # Month mapping
                month_map = {
                    "كانون الأول": 12,
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
                }

                month = month_map.get(month_name)
                if month:
                    dt = datetime(year, month, day, hour, minute)
                    return dt.strftime("%Y-%m-%d %H:%M:%S")

        except Exception as e:
            print(f"Error parsing date: {e}")

        return None


if __name__ == "__main__":
    crawler = LDebate()
    crawler.download_articles_links()
    crawler.download_articles()
    CrawlerLog.add_log(
        crawler_id=crawler.crawler_id,
        log_level="INFO",
        message=f"Articles Downloaded: {crawler.scraped_articles}",
    )
    # TEMPORARILY DISABLED: Temporary folder cleanup for image downloads
    # base_dir = os.path.dirname(os.path.abspath(__file__))
    # tmp_folder = os.path.join(base_dir, "tmp")
    # if os.path.exists(tmp_folder):
    #     shutil.rmtree(tmp_folder)
