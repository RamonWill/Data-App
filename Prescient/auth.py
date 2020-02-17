from Prescient import app, db

from flask import (Blueprint, flash,
                   redirect, render_template,
                   url_for)
from .models import User
from flask_login import current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from . import forms
# this is a routes.py file aka a View

bp = Blueprint("auth", __name__, url_prefix="/auth")

@app.route('/')
def index():
    return render_template("test.html")


@bp.route("/register", methods=("GET", "POST"))
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = forms.RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = generate_password_hash(form.password.data)
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Your account has now been created!")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", title="Register", form=form)


@bp.route("/login", methods=("GET", "POST"))
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = forms.LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None:
            flash("Invalid username or password")
            return redirect(url_for("auth.login"))
        check = check_password_hash(user.password, form.password.data)
        if not check:
            flash("Invalid username or password")
            return redirect(url_for("auth.login"))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for("index"))
    return render_template("auth/login.html", title="Log In", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
