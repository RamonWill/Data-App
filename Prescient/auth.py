import functools

from flask import(Blueprint, flash, g, redirect,
                  render_template, request, session,
                  url_for)

from werkzeug.security import check_password_hash, generate_password_hash
from Prescient.db import get_db
from . import forms
bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=("GET", "POST"))
def register():
    form = forms.RegistrationForm(request.form)
    if request.method == "POST" and form.validate():
        username = form.username.data
        password = form.password.data
        db = get_db()
        error = None

        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."
        elif db.execute(
            "SELECT id FROM login_details WHERE username = ?", (username,)
        ).fetchone() is not None:
            error = "User {} is already registered.".format(username)

        if error is None:
            db.execute(
                "INSERT INTO login_details (username, password) VALUES (?, ?)",
                (username, generate_password_hash(password))
            )
            db.commit()
            return redirect(url_for("auth.login"))

        flash(error)

    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=("GET", "POST"))
def login():
    form = forms.LoginForm(request.form)
    if request.method == "POST" and form.validate():
        username = form.username.data
        password = form.password.data
        db = get_db()
        error = None
        user = db.execute(
            "SELECT * FROM login_details WHERE username = ?", (username,)
        ).fetchone()

        if user is None:
            error = "Incorrect username or password."
        elif not check_password_hash(user["password"], password):
            error = "Incorrect username or password."

        if error is None:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("dashboard"))

        flash(error)

    return render_template("auth/login.html", form=form)


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM login_details WHERE id = ?', (user_id,)
        ).fetchone()


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
