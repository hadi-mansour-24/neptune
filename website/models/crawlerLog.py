from website import db
from datetime import datetime


class CrawlerLog(db.Model):
    __tablename__ = "crawler_log"

    log_id = db.Column(db.Integer, primary_key=True)
    crawler_id = db.Column(db.Integer, db.ForeignKey("crawler.crawler_id"))
    log_level = db.Column(db.String(50))
    message = db.Column(db.Text)
    log_time = db.Column(db.DateTime, default=datetime.now())

    def clear_all():
        """Delete all logs from the database."""
        try:
            query = CrawlerLog.query
            num_deleted = query.delete()
            db.session.commit()
            return True, num_deleted
        except Exception as e:
            db.session.rollback()
            return False, str(e)
