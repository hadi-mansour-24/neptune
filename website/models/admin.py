from website import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class Admin(db.Model):
    __tablename__ = "admin"
    admin_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="admin")
    created_at = db.Column(db.DateTime, default=datetime.now())

    def change_username(admin_id, new_username):
        admin = Admin.query.filter_by(admin_id=admin_id).first()

        if not admin:
            return "Admin not found!"

        if new_username == Admin.query.filter_by(username=new_username).first():
            return "Username already exists!"

        admin.username = new_username
        try:
            db.session.commit()
            return f"Username updated successfully to {new_username}!"
        except Exception as e:
            db.session.rollback()
            return "Error occured updating username!"
        finally:
            db.session.close()

    def change_password(admin_id, old_password, new_password):
        admin = Admin.query.filter_by(admin_id=admin_id).first()
        if not admin:
            return "Admin not found!"
        if not check_password_hash(admin.password_hash, old_password):
            return "Current password is incorrect!"

        admin.password_hash = generate_password_hash(new_password)
        try:
            db.session.commit()
            return "Password updated successfully!"
        except:
            db.session.rollback()
            return "Error occurred updating password!"
        finally:
            db.session.close()
