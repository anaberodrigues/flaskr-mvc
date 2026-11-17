import functools

from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from .models import User, db
from .uploads import salvar_imagem

bp = Blueprint("auth", __name__, url_prefix="/auth")


def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    """Carrega o usuário logado (objeto User) em g.user."""
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = db.session.get(User, user_id)


@bp.route("/register", methods=("GET", "POST"))
def register():
    """Registra um novo usuário, com foto de perfil opcional."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        error = None

        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."

        avatar = None
        if error is None:
            try:
                avatar = salvar_imagem(request.files.get("avatar"))
            except ValueError as e:
                error = str(e)

        if error is None:
            user = User(
                username=username,
                password=generate_password_hash(password),
                avatar=avatar,
            )
            db.session.add(user)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                error = f"User {username} is already registered."
            else:
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    """Faz login adicionando o id do usuário na sessão."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        error = None
        user = db.session.execute(
            db.select(User).filter_by(username=username)
        ).scalar_one_or_none()

        if user is None:
            error = "Incorrect username."
        elif not check_password_hash(user.password, password):
            error = "Incorrect password."

        if error is None:
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("index"))

        flash(error)

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    """Limpa a sessão."""
    session.clear()
    return redirect(url_for("index"))