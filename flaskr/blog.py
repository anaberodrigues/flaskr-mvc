from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort

from .auth import login_required
from .models import Post, db
from .uploads import remover_imagem, salvar_imagem

bp = Blueprint("blog", __name__)


@bp.route("/")
def index():
    """Mostra todos os posts, do mais recente para o mais antigo."""
    posts = db.session.execute(
        db.select(Post).order_by(Post.created.desc())
    ).scalars().all()
    return render_template("blog/index.html", posts=posts)


def get_post(id, check_author=True):
    """Busca um post pelo id (404 se não existir, 403 se não for o autor)."""
    post = db.session.get(Post, id)

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post.author_id != g.user.id:
        abort(403)

    return post


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    """Cria um post para o usuário atual, com imagem opcional."""
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        imagem = None
        if error is None:
            try:
                imagem = salvar_imagem(request.files.get("imagem_post"))
            except ValueError as e:
                error = str(e)

        if error is not None:
            flash(error)
        else:
            post = Post(title=title, body=body, author_id=g.user.id, imagem_post=imagem)
            db.session.add(post)
            db.session.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    """Atualiza um post se o usuário atual for o autor."""
    post = get_post(id)

    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        nova_imagem = None
        if error is None:
            try:
                nova_imagem = salvar_imagem(request.files.get("imagem_post"))
            except ValueError as e:
                error = str(e)

        if error is not None:
            flash(error)
        else:
            post.title = title
            post.body = body
            if nova_imagem:
                remover_imagem(post.imagem_post)  
                post.imagem_post = nova_imagem
            db.session.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/update.html", post=post)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    """Apaga o post (e a imagem dele) se o usuário for o autor."""
    post = get_post(id)
    remover_imagem(post.imagem_post)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for("blog.index"))