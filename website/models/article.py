from website import db
from datetime import datetime


class Article(db.Model):
    __tablename__ = "article"

    article_id = db.Column(db.Integer, primary_key=True)
    crawler_id = db.Column(db.Integer, db.ForeignKey("crawler.crawler_id"))
    entry_id = db.Column(db.Text, unique=True)
    title = db.Column(db.Text)
    content = db.Column(db.Text)
    article_url = db.Column(db.Text)
    has_media = db.Column(db.Boolean)
    publish_date = db.Column(db.DateTime)
    archive_date = db.Column(db.DateTime, default=datetime.now())
