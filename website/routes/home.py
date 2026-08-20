from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    jsonify,
    request,
    current_app,
    send_file,
    flash,
)
from website.models.article import Article
from website.models.crawler import Crawler
from website.models.favorite import Favorite
from website.models.admin import Admin
from website import db
import pandas as pd
import tempfile
import zipfile
import shutil
import os

bp = Blueprint("home", __name__)


@bp.route("/home")
def index():
    """Renders the home.html page and passes parameters needed to the page"""
    """User is redirected to the login page if not logged in"""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # Get user role for navbar
    user = Admin.query.get(session["user_id"])
    if user:
        if user.role == "admin" or user.role == "super":
            is_admin = True
        else:
            is_admin = False

    # Query and pass all the crawlers to home page template
    # so its dropdown can be filled with available crawlers (available pages)
    crawlers = Crawler.query.all()
    return render_template(
        "home.html", is_logged_in=True, crawlers=crawlers, is_admin=is_admin
    )


@bp.route("/search_articles")
def search_articles():
    """Allows the user to search with multiple criteria including:
    - Source of articles
    - Keywords in content OR title of articles
    - Articles between two date ranges
    """
    """Returns 5 Articles per page and applies pagination
        to avoid overloading the system
    """
    if "user_id" not in session:
        return jsonify({}), 401

    # Get the criteria of searching from the URL fetched by the user
    source = request.args.get("source")
    keyword = request.args.get("keyword")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    # Start a query to build using SQLAlchemy
    query = Article.query

    # Search with source if entered
    if source:
        crawler = Crawler.query.filter(Crawler.name.ilike(f"%{source}%")).first()
        if not crawler:
            return jsonify({"articles": [], "page": 1, "total_pages": 0})
        query = query.filter(Article.crawler_id == crawler.crawler_id)

    # Search by keyword if entered
    if keyword:
        query = query.filter(
            Article.title.ilike(f"%{keyword}%") | Article.content.ilike(f"%{keyword}%")
        )

    # Date ranges both should be present if the user chooses to search by date range
    # The search is in the publish date and not the archive date
    if start_date and end_date:
        query = query.filter(Article.publish_date.between(start_date, end_date))

    # Execute the filtered query according to the publish date in descending order
    # GET ONLY 5 ARTICLES AND NOT THE WHOLE ARTICLE TABLE
    # (PAGE -> PAGE NUMBER, PER_PAGE -> AMOUNT OF ARTICLES TO FETCH)
    paginated = query.order_by(Article.publish_date.desc()).paginate(
        page=page, per_page=per_page
    )

    # Build the result list
    results = []
    for article in paginated.items:  # Only articles fetched with pagination (5)
        crawler = Crawler.query.get(article.crawler_id)
        crawler_name = crawler.name if crawler else "UNKNOWN"

        # TEMPORARILY DISABLED: Start building the images list which contains the images paths
        # images = []
        # # If article scraped has_media = True
        # if article.has_media:
        #     folder = os.path.join(current_app.static_folder, "media", article.entry_id)
        #     if os.path.exists(folder):
        #         # Loop inside the files in the folder folder
        #         for f in os.listdir(folder):
        #             if f.lower().endswith(
        #                 (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp")
        #             ):
        #                 # Build the URL of the image
        #                 images.append(
        #                     url_for("static", filename=f"media/{article.entry_id}/{f}")
        #                 )
        # TEMPORARILY DISABLED: Empty list for text-only content display
        images = []
        # Append the results with data
        results.append(
            {
                "article_id": article.entry_id,
                "source": crawler_name,
                "title": article.title,
                "article_url": article.article_url,
                "content": article.content,
                "has_media": article.has_media,
                "images": images,
                "publish_date": (article.publish_date.strftime("%Y-%m-%d")),
                "archive_date": (article.archive_date.strftime("%Y-%m-%d")),
            }
        )

    # Convert the results list into json and return it to the client requesting the endpoint
    return jsonify(
        {"articles": results, "page": paginated.page, "total_pages": paginated.pages}
    )


# TEMPORARILY DISABLED: Media/image upload API endpoint - feature disabled for text-only content
# @bp.route("/upload_media/<article_id>", methods=["POST"])
# def upload_media(article_id):
#     """This function recieves from the crawler the media sent to it
#     and saves them inside the static/media/entry-id file
#     where it should be to be displayed later on on the home page
#     """
#     file = request.files.get("file")
#     if not file:
#         return jsonify({"status": "error", "message": "No file"}), 400
#
#     folder = os.path.join(current_app.static_folder, "media", article_id)
#     os.makedirs(folder, exist_ok=True)
#     file.save(os.path.join(folder, file.filename))
#
#     return jsonify({"status": "success"})


@bp.route("/export_excel")
def export_excel():
    """Exports selected articles from the home page (checkboxes) as excel
    and with their media as well, ZIPs the final folder and return it to the user"""

    ids = request.args.get("ids")
    articles = Article.query.filter(Article.entry_id.in_(ids.split(","))).all()

    if not articles:
        return "No articles to export", 400  # 400 status code response -> Bad request

    # Create a temporary folder to store the excel and media file innit
    temp_dir = tempfile.mkdtemp()

    try:
        # Create an excel file inside the temporary folder and name it articles
        excel_path = os.path.join(temp_dir, "articles.xlsx")

        # Create a data frame and append the data to it using pandas library
        df = pd.DataFrame(
            [
                {
                    "Title": a.title,
                    "Content": a.content,
                    "Publish Date": (
                        a.publish_date.strftime("%Y-%m-%d") if a.publish_date else ""
                    ),
                    "Source URL": a.article_url,
                    "Article ID": a.entry_id,
                    "Has Images": "Yes" if a.has_media else "No",
                }
                for a in articles
            ]
        )

        # Save the excel to its path
        df.to_excel(excel_path, index=False)

        # Create the images folder to join it to the temporary folder that contains the excel file
        images_dir = os.path.join(temp_dir, "media")
        os.makedirs(images_dir, exist_ok=True)

        # TEMPORARILY DISABLED: Copy images to export folder - media feature disabled
        # for a in articles:
        #     if a.has_media:
        #         folder = os.path.join(current_app.static_folder, "media", a.entry_id)
        #         if os.path.exists(folder):
        #             for img in os.listdir(folder):
        #                 if img.lower().endswith(
        #                     (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp")
        #                 ):
        #                     shutil.copy2(
        #                         os.path.join(folder, img),  # Source file to copy from
        #                         os.path.join(
        #                             images_dir, f"{a.entry_id}_{img}"
        #                         ),  # Destination file to copy to
        #                     )

        # I am obligated to zip the file since the normal folder can't be exported
        # Create the zip file path
        zip_path = os.path.join(temp_dir, "export.zip")
        # Open ZIP file
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Write the excel file to it
            zipf.write(excel_path, "articles.xlsx")
            # Iterating through the images in the images_dir and adding them to the zip file
            for root, dirs, files in os.walk(images_dir):
                for f in files:
                    path = os.path.join(root, f)
                    zipf.write(path, os.path.relpath(path, temp_dir))

        # Send the file from server to the client (download the zip file)
        return send_file(
            zip_path, as_attachment=True, download_name="articles_export.zip"
        )

    finally:
        # Delete the temporary folder we previously created
        shutil.rmtree(temp_dir, ignore_errors=True)


@bp.route("/add_favorites", methods=["POST"])
def add_favorites():
    # If the user not logged in redirect him to the login page
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    # Get the list of the ids of articles requested to be favorites
    article_ids = request.form.getlist("article_ids")

    # Return error if no articles are selected
    if not article_ids:
        return jsonify({"success": False, "message": "No articles selected"}), 400

    # Track the count of the already favorited articles and the freshly favorited ones
    added_count = 0
    already_count = 0

    try:
        for article_id in article_ids:
            exists = Favorite.query.filter_by(
                admin_id=session["user_id"], article_id=article_id
            ).first()

            if exists:
                already_count += 1
            else:
                db.session.add(
                    Favorite(admin_id=session["user_id"], article_id=article_id)
                )
                added_count += 1

        db.session.commit()
        message = f"Added {added_count} article(s)"
        if already_count > 0:
            message += f". {already_count} already existed."

        return jsonify({"success": True, "message": message}), 200

    except Exception as e:
        return jsonify({"success": False, "message": "Error adding to favorites"}), 500
