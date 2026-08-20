from website import db
from datetime import datetime


class Favorite(db.Model):
    __tablename__ = "favorite"

    favorite_id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admin.admin_id"))
    article_id = db.Column(db.Text, db.ForeignKey("article.article_id"))
    favourited_at = db.Column(db.DateTime, default=datetime.now())
