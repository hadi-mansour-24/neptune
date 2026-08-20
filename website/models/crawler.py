from website import db
from datetime import datetime


class Crawler(db.Model):
    __tablename__ = "crawler"

    crawler_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    last_seen = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now())
