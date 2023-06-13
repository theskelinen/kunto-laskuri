from flask import Blueprint, render_template, request

routes = Blueprint("routes", __name__)

@routes.route("/")
def index():
    return render_template("home.html")

@routes.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")