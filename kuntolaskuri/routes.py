from flask import Blueprint, render_template, request, redirect
import kuntolaskuri.users as users

routes = Blueprint("routes", __name__)

@routes.route("/")
def index():
    return render_template("home.html")

@routes.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if users.login(username, password):
            return redirect("/")
        else:
            return render_template("login.html")

@routes.route("/sign-up", methods=["GET", "POST"])
def sign_up():
    if request.method == "GET":
        return render_template("sign_up.html")
    if request.method == "POST":
        username = request.form["username"]
        password1 = request.form["password1"]
        password2 = request.form["password2"]
        if password1 != password2:
            return render_template("sign_up.html")
        if users.register(username, password1):
            return redirect("/")
        else:
            return render_template("sign_up.html")

@routes.route("/user_page", methods=["GET"])
def user_page():
    if request.method == "GET":
        return render_template("user_page.html")