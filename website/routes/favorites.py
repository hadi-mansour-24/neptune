from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    jsonify,
    current_app,
    url_for,
    flash,
)
from website.models.favorite import Favorite
from website.models.article import Article
from website.models.crawler import Crawler
from website.models.admin import Admin
from website import db
import os

bp = Blueprint("favorites", __name__)


@bp.route("/favorites")
def favorites():
    """Display favorited articles."""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # Get user role for navbar
    user = Admin.query.get(session["user_id"])
    if user:
        if user.role == "admin" or user.role == "super":
            is_admin = True
        else:
            is_admin = False

    return render_template("favorites.html", is_logged_in=True, is_admin=is_admin)


@bp.route("/get_favorites")
def get_favorites():
    """Get favorite articles for current user."""
    if "user_id" not in session:
        return jsonify([]), 401

    # Get favorites for current user
    favorites = Favorite.query.filter_by(admin_id=session["user_id"]).all()

    results = []
    for fav in favorites:
        # Get the article details
        article = Article.query.filter_by(entry_id=fav.article_id).first()
        if article:
            # Get crawler name
            crawler = Crawler.query.get(article.crawler_id)
            crawler_name = crawler.name if crawler else "UNKNOWN"

            # TEMPORARILY DISABLED: Get images if available - media feature disabled
            # images = []
            # if article.has_media:
            #     folder_name = article.entry_id
            #     folder_path = os.path.join(
            #         current_app.static_folder, "media", folder_name
            #     )
            #
            #     if os.path.exists(folder_path):
            #         for file in os.listdir(folder_path):
            #             if file.lower().endswith(
            #                 (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp")
            #             ):
            #                 img_url = url_for(
            #                     "static", filename=f"media/{folder_name}/{file}"
            #                 )
            #                 images.append(img_url)
            # TEMPORARILY DISABLED: Empty images list for text-only content
            images = []

            results.append(
                {
                    "article_id": article.entry_id,
                    "source": crawler_name,
                    "title": article.title,
                    "article_url": article.article_url,
                    "content": article.content,
                    "has_media": article.has_media,
                    "images": images,
                    "publish_date": article.publish_date.strftime("%Y-%m-%d"),
                    "archive_date": article.archive_date.strftime("%Y-%m-%d"),
                    "favorited_at": fav.favourited_at.strftime("%Y-%m-%d %H:%M"),
                }
            )

    return jsonify(results)


@bp.route("/remove_favorite/<article_id>", methods=["DELETE"])
def remove_favorite(article_id):
    """Remove article from favorites."""
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    try:
        favorite = Favorite.query.filter_by(
            admin_id=session["user_id"], article_id=article_id
        ).first()

        if favorite:
            db.session.delete(favorite)
            db.session.commit()
            return jsonify({"success": True, "message": "Removed from favorites"})
        else:
            return jsonify({"success": False, "message": "Favorite not found"})

    except Exception as e:
        print(f"Error removing favorite: {e}")
        return jsonify({"success": False, "message": "Database error"}), 500


@bp.route("/export_favorites")
def export_favorites():
    """Export all favorite articles using existing export_excel method."""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # Get all favorite article IDs for current user
    favorites = Favorite.query.filter_by(admin_id=session["user_id"]).all()

    if not favorites:
        flash("No favorite articles to export", "warning")
        return redirect(url_for("favorites.favorites"))

    # Create a list of ids to pass it to the existing method of exporting
    article_ids = [fav.article_id for fav in favorites]
    ids_string = ",".join(article_ids)

    # Redirect to existing export route with passing the IDs
    return redirect(url_for("home.export_excel", ids=ids_string))
