from website import db
from datetime import datetime


class Activity(db.Model):
    __tablename__ = "Activity"
    activity_id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admin.admin_id"))
    activity_details = db.Column(db.String(255), nullable=False)
    activity_date = db.Column(db.DateTime, default=datetime.now())

    # def add_new_log(admin_id, activity_details, activity_date):
