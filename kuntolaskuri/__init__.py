from flask import Flask
from os import getenv
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = getenv("SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
    db.init_app(app)

    from kuntolaskuri.routes import routes

    app.register_blueprint(routes, url_prefix="/")

    return app
