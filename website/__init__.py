from flask import Flask
from .config import Config  # Import Config class which contains app settings
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

# Initialize SQLAlchemy
# SQLAlchemy is a library lets us to work
# with database using methods instead of writing normal SQL queries
db = SQLAlchemy()


def create_app():
    # Create a Flask app object
    app = Flask(__name__)

    # Load settings from Config class to the Flask applivation
    app.config.from_object(Config)

    # Initialize the database in this app
    # Connects SQLAlchemy with this Flask app
    db.init_app(app)

    # import the blueprints
    from website.routes.auth import bp as auth_bp
    from website.routes.favorites import bp as fav_bp
    from website.routes.management import bp as management_bp
    from website.routes.home import bp as home_bp

    # Add blueprints to the Flask application
    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(fav_bp)
    app.register_blueprint(management_bp)

    # Create a default user when the program runs
    with app.app_context():
        from .models.admin import Admin

        if not Admin.query.filter_by(username="1hadymansour").first():
            user = Admin(
                username="1hadymansour",
                password_hash=generate_password_hash("1hadymansour"),
                role="admin",
            )
            db.session.add(user)
            db.session.commit()

    # Return the app so it can be used in run.py
    return app
