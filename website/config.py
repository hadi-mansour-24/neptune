import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "neptune128")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "SQLALCHEMY_DATABASE_URI",
        "mysql+pymysql://neptune_user:neptunized128@localhost/neptune?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
