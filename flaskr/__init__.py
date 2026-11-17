import os

import click
from flask import Flask

from .models import db


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///flaskr.sqlite",
        UPLOAD_FOLDER=os.path.join(app.root_path, "static", "uploads"),
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    @app.route("/hello")
    def hello():
        return "Hello, World!"

    db.init_app(app)
    with app.app_context():
        db.create_all()

    @app.cli.command("init-db")
    def init_db_command():
        """Apaga tudo e recria as tabelas."""
        db.drop_all()
        db.create_all()
        click.echo("Initialized the database.")

    from . import auth
    from . import blog
    from . import calculos

    app.register_blueprint(auth.bp)
    app.register_blueprint(blog.bp)
    app.register_blueprint(calculos.bp)

    app.add_url_rule("/", endpoint="index")

    return app