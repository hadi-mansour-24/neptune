import os
from website import create_app, db
from website.models.admin import Admin
from website.models.article import Article
from website.models.favorite import Favorite
from website.models.crawler import Crawler
from website.models.crawlerLog import CrawlerLog
from website.models.activity import Activity

app = create_app()

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
