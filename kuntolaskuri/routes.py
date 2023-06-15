from flask import Blueprint, render_template, request, redirect, flash
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
            flash("Tervetuloa!", category="success")
            return redirect("/")
        else:
            flash("Sisäänkirjaus epäonnistui", category="error")
        return render_template("login.html")

@routes.route("/logout")
def logout():
    users.logout()
    flash("Hei Hei!", category="success")
    return redirect("/")

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
            flash("Käyttäjä luotu!", category="success")
            return redirect("/")
        else:
            flash("Rekisteröinti epäonnistui", category="error")
        return render_template("sign_up.html")

@routes.route("/user_page", methods=["GET"])
def user_page():
    if request.method == "GET":
        user = users.get_information()
        #first_name = user[0]
        #last_name = user[1]
        #age = user[2]
        #sex = user[3]
        return render_template("user_page.html", user=user)

@routes.route("/user_page/update", methods=["GET", "POST"])
def update_user():
    if request.method == "GET":
        return render_template("update_user.html")
    if request.method == "POST":
        id_user = users.session["user_id"]
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        age = request.form["age"]
        sex = request.form["sex"]
        check_input = users.check_input(first_name, last_name, age, sex)
        if check_input != "All good everything":
            flash(check_input, category="error")
            return render_template("update_user.html")
        if users.user_update(first_name, last_name, age, sex, id_user):
            flash("Tiedot tallennettu", category="success")
            return redirect("/user_page")
        else:
            flash("Tietojen tallennus epäonnistui", category="error")
    return render_template("update_user.html")