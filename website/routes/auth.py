from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from werkzeug.security import check_password_hash
from website.models.admin import Admin

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if "user_id" in session:
        flash("You're already logged in")
        return redirect(url_for("home.index"))
    
    if request.method == 'POST':
        user = Admin.query.filter_by(username=request.form['username']).first()

        if user and check_password_hash(user.password_hash, request.form['password']):
            session['user_id'] = user.admin_id
            session['username'] = user.username
            return redirect(url_for('home.index'))
        else:
            flash('Invalid credentials', "danger")

    return render_template('login.html', is_logged_in=False)


@bp.route('/logout')
def logout():
    if "user_id" not in session:
        flash("You're not logged in initially!")
        return redirect(url_for("auth.login"))
    
    session.clear()
    return redirect(url_for('auth.login'))
