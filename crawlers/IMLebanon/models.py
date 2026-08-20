from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    String,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from config import DB_URL
import pytz

beirut_tz = pytz.timezone("Asia/Beirut")
engine = create_engine(DB_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)


class Article(Base):
    __tablename__ = "article"

    article_id = Column(Integer, primary_key=True)
    crawler_id = Column(Integer, ForeignKey("crawler.crawler_id"))
    entry_id = Column(Text)
    title = Column(Text)
    content = Column(Text)
    article_url = Column(Text)
    has_media = Column(Boolean)
    publish_date = Column(DateTime)
    archive_date = Column(DateTime, default=datetime.now(beirut_tz))

    def add_article(
        crawler_id, entry_id, title, content, article_url, has_media, publish_date
    ):
        session = Session()
        try:
            new_article = Article(
                crawler_id=crawler_id,
                entry_id=entry_id,
                title=title,
                content=content,
                article_url=article_url,
                has_media=has_media,
                publish_date=publish_date,
            )
            session.add(new_article)
            session.commit()
            session.refresh(new_article)
            return new_article.article_id
        except Exception as e:
            print("Error occured inserting article: ", e)
            session.rollback()
            return None
        finally:
            session.close()


class Crawler(Base):
    __tablename__ = "crawler"

    crawler_id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)
    last_seen = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now(beirut_tz))

    def get_crawler_id(crawler_name):
        session = Session()
        try:
            crawler = session.query(Crawler).filter_by(name=crawler_name).first()

            if crawler:
                return crawler.crawler_id

            new_crawler = Crawler(name=crawler_name)
            session.add(new_crawler)
            session.commit()
            session.refresh(new_crawler)
            return new_crawler.crawler_id

        except Exception as e:
            print("Error occured fetching crawler id: ", e)
            session.rollback()
            return None
        finally:
            session.close()

    def update_crawler_last_seen(crawler_name):
        session = Session()
        try:
            crawler = session.query(Crawler).filter_by(name=crawler_name).first()
            if crawler:
                crawler.last_seen = datetime.now(beirut_tz)
                session.commit()
                return True
            return False
        except Exception as e:
            print("Error updating last seen: ", e)
            session.rollback()
            return False
        finally:
            session.close()


class CrawlerLog(Base):
    __tablename__ = "crawler_log"

    log_id = Column(Integer, primary_key=True)
    crawler_id = Column(Integer, ForeignKey("crawler.crawler_id"))
    log_level = Column(String(255))
    message = Column(String(255))
    log_time = Column(DateTime, default=datetime.now(beirut_tz))

    def add_log(crawler_id, log_level, message):
        session = Session()
        try:
            new_log = CrawlerLog(
                crawler_id=crawler_id, log_level=log_level, message=message
            )
            session.add(new_log)
            session.commit()
            session.refresh(new_log)
            return new_log.log_id
        except Exception as e:
            print("Error occured inserting the crawler log: ", e)
            session.rollback()
            return None
        finally:
            session.close()
