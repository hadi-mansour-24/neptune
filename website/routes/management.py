from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    jsonify,
    request,
    flash,
    send_file,
)
import io
import csv
import sys
import subprocess
from datetime import datetime
from website.models.admin import Admin
from website.models.crawler import Crawler
from website.models.crawlerLog import CrawlerLog

bp = Blueprint("management", __name__)

# Dictionary to track running crawler processes
active_crawlers = {}


# Route to render Management page
@bp.route("/management")
def management():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = Admin.query.get(session["user_id"])
    if user:
        if user.role == "admin" or user.role == "super":
            is_admin = True
        else:
            is_admin = False

    # Check if user is admin
    if not is_admin:
        flash("Access denied. Only administrators can access this page.", "error")
        return redirect(url_for("home.index"))

    is_admin = user.role == "super" or user.role == "admin" if user else False

    crawlers = Crawler.query.all()
    crawler_logs = CrawlerLog.query.order_by(CrawlerLog.log_time.desc()).all()

    return render_template(
        "management.html",
        is_logged_in=True,
        is_admin=is_admin,
        crawlers=crawlers,
        crawler_logs=crawler_logs,
        current_user=user.username,
    )


@bp.route("/get_crawlers")
def get_crawlers():

    if "user_id" not in session:
        return jsonify({"success": False, "logs": []}), 401

    crawlers = Crawler.query.all()
    data = []
    for crawler in crawlers:
        item = {
            "id": crawler.crawler_id,
            "name": crawler.name,
            "last_seen": (crawler.last_seen.strftime("%Y-%m-%d %H:%M")),
        }
        data.append(item)

    return jsonify({"success": True, "crawlers": data})


@bp.route("/get_current_user")
def get_current_user():
    """Get current user info."""
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    user = Admin.query.get(session["user_id"])
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    return jsonify({"success": True, "username": user.username, "role": user.role})


@bp.route("/get_logs_count")
def get_logs_count():
    """Get total number of logs."""
    if "user_id" not in session:
        return jsonify({"success": False, "count": 0}), 401

    count = CrawlerLog.query.count()
    return jsonify({"success": True, "count": count})


@bp.route("/export_logs")
def export_logs():
    """Export logs as CSV."""
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    logs = CrawlerLog.query.order_by(CrawlerLog.log_time.desc()).all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(["Timestamp", "Crawler", "Level", "Message"])

    # Write data
    for log in logs:
        crawler = Crawler.query.get(log.crawler_id)
        crawler_name = crawler.name if crawler else "Unknown"
        writer.writerow(
            [
                log.log_time.strftime("%Y-%m-%d %H:%M:%S"),
                crawler_name,
                log.log_level,
                log.message,
            ]
        )

    # Create response
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f'logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
    )


@bp.route("/get_logs")
def get_logs():

    if "user_id" not in session:
        return jsonify({"success": False, "logs": []}), 401

    logs = CrawlerLog.query.order_by(CrawlerLog.log_time.desc()).all()
    data = []
    for log in logs:
        crawler = Crawler.query.get(log.crawler_id)
        item = {
            "timestamp": log.log_time.strftime("%Y-%m-%d %H:%M"),
            "journal": crawler.name,
            "level": log.log_level,
            "message": log.message,
        }
        data.append(item)

    return jsonify({"success": True, "logs": data})


@bp.route("/run_crawler", methods=["POST"])
def run_crawler_route():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    data = request.get_json()
    crawler_id = data.get("crawler_id")
    if not crawler_id:
        return jsonify({"success": False, "message": "Missing crawler ID"}), 400

    crawler = Crawler.query.get(crawler_id)
    if not crawler:
        return jsonify({"success": False, "message": "Crawler not found"}), 404

    # Check if crawler is already running
    if crawler_id in active_crawlers:
        process = active_crawlers[crawler_id]
        if process.poll() is None:  # Process is still running
            return (
                jsonify(
                    {"success": False, "message": f"{crawler.name} is already running"}
                ),
                400,
            )
        else:
            # Process finished, remove from tracking
            del active_crawlers[crawler_id]

    # Map crawler names to their script paths
    crawler_scripts = {
        "IMLebanon": "crawlers/IMLebanon/IMLebanon.py",
        "Lebanon Debate": "crawlers/LebanonDebate/LebanonDebate.py",
        "Al-Akhbar": "crawlers/Al-Akhbar/al-akhbar.py",
    }

    crawler_script = crawler_scripts.get(crawler.name)
    if not crawler_script:
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"No script found for crawler: {crawler.name}",
                }
            ),
            404,
        )

    try:
        # Update last seen time
        crawler.last_seen = datetime.now()
        from website import db

        db.session.commit()

        # Run the script in a separate process
        process = subprocess.Popen([sys.executable, crawler_script])

        # Track the process
        active_crawlers[crawler_id] = process

        # Log the crawler start
        log_entry = CrawlerLog(
            crawler_id=crawler_id,
            log_level="INFO",
            message=f"Crawler '{crawler.name}' started manually by {session['username']}",
        )
        db.session.add(log_entry)
        db.session.commit()

        return jsonify(
            {"success": True, "message": f"{crawler.name} started successfully"}
        )
    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Error starting crawler: {str(e)}"}),
            500,
        )


@bp.route("/add_crawler", methods=["POST"])
def add_crawler():
    """Add a new crawler"""
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    user = Admin.query.get(session["user_id"])
    if user:
        if user.role == "super":
            is_super = True
        else:
            is_super = False

    if not is_super:
        return jsonify({"success": False, "message": "Developer access required"}), 403

    data = request.get_json()
    crawler_name = data.get("name")

    if not crawler_name:
        return jsonify({"success": False, "message": "Crawler name required"}), 400

    # Check if crawler already exists
    existing_crawler = Crawler.query.filter_by(name=crawler_name).first()
    if existing_crawler:
        return jsonify({"success": False, "message": "Crawler already exists"}), 400

    try:
        # Create new crawler entry
        new_crawler = Crawler(name=crawler_name, last_seen=datetime.now())
        from website import db

        db.session.add(new_crawler)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Crawler '{crawler_name}' added successfully",
                    "crawler": {
                        "id": new_crawler.crawler_id,
                        "name": new_crawler.name,
                        "last_seen": new_crawler.last_seen.strftime("%Y-%m-%d %H:%M"),
                    },
                }
            ),
            201,
        )
    except Exception as e:
        db.session.rollback()
        return (
            jsonify({"success": False, "message": f"Error adding crawler: {str(e)}"}),
            500,
        )


@bp.route("/clear_logs", methods=["DELETE"])
def clear_logs():
    """Clear all system logs."""
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    success, result = CrawlerLog.clear_all()
    if success:
        return jsonify({"success": True, "message": f"{result} logs cleared"})
    else:
        return jsonify({"success": False, "message": result}), 500


@bp.route("/change_username", methods=["POST"])
def change_username():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    data = request.get_json()
    new_username = data.get("new_username")

    if not new_username:
        return jsonify({"success": False, "message": "All fields are required"})

    message = Admin.change_username(session["user_id"], new_username)
    session["username"] = new_username
    return jsonify({"success": "successfully" in message.lower(), "message": message})


@bp.route("/change_password", methods=["POST"])
def change_password():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    data = request.get_json()
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not old_password or not new_password:
        return jsonify({"success": False, "message": "All fields are required"})

    message = Admin.change_password(session["user_id"], old_password, new_password)
    return jsonify({"success": "successfully" in message.lower(), "message": message})


@bp.route("/get_users")
def get_users():
    """Get all users"""
    if "user_id" not in session:
        return jsonify({"success": False, "users": []}), 401

    users = Admin.query.filter_by().all()
    data = []
    for user in users:
        item = {
            "id": user.admin_id,
            "username": user.username,
            "role": user.role,
            "created_at": (
                user.created_at.strftime("%Y-%m-%d %H:%M") if user.created_at else "N/A"
            ),
        }
        data.append(item)

    return jsonify({"success": True, "users": data})


@bp.route("/create_user", methods=["POST"])
def create_user():
    """Create a new user account."""
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    current_user = Admin.query.get(session["user_id"])
    if current_user:
        if current_user.role == "admin" or current_user.role == "super":
            is_admin = True
        else:
            is_admin = False
    if not is_admin:
        return jsonify({"success": False, "message": "Admin access required"}), 403

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "user")

    # Validate role
    valid_roles = ["admin", "user"]
    if role not in valid_roles:
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Invalid role. Must be one of: {', '.join(valid_roles)}",
                }
            ),
            400,
        )

    if not username or not password:
        return (
            jsonify(
                {"success": False, "message": "Username and password are required"}
            ),
            400,
        )

    # Check if username already exists
    existing_user = Admin.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"success": False, "message": "Username already exists"}), 400

    try:
        from werkzeug.security import generate_password_hash

        new_user = Admin(
            username=username,
            password_hash=generate_password_hash(password),
            role=role,
        )
        from website import db

        db.session.add(new_user)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"User '{username}' created successfully as {role}",
                    "user": {
                        "id": new_user.admin_id,
                        "username": new_user.username,
                        "role": new_user.role,
                        "created_at": (
                            new_user.created_at.strftime("%Y-%m-%d %H:%M")
                            if new_user.created_at
                            else "N/A"
                        ),
                    },
                }
            ),
            201,
        )
    except Exception as e:
        db.session.rollback()
        return (
            jsonify({"success": False, "message": f"Error creating user: {str(e)}"}),
            500,
        )


@bp.route("/delete_user/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    """Delete a user account."""
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    user = Admin.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    current_user = Admin.query.get(session["user_id"])
    if current_user:
        if current_user.role == "super":
            is_super = True
        else:
            is_super = False

    if not is_super:
        return jsonify({"success": False, "message": "Developer access required"}), 403
    elif user.role == "super":
        return jsonify({"success": False, "message": "Cannot delete super admin"}), 403
    elif user.admin_id == current_user.admin_id:
        return (
            jsonify({"success": False, "message": "Cannot delete your own account"}),
            403,
        )
    try:
        from website import db

        db.session.delete(user)
        db.session.commit()
        return jsonify({"success": True, "message": "User deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return (
            jsonify({"success": False, "message": f"Error deleting user: {str(e)}"}),
            500,
        )
