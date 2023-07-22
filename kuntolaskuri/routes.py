from flask import Blueprint, render_template, request, redirect, flash, abort
import kuntolaskuri.users as users
import kuntolaskuri.tests as tests

routes = Blueprint("routes", __name__)

@routes.route("/")
def index():
    return render_template("home.html")

@routes.route("/faq_page")
def faq():
    return render_template("faq.html")

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
            flash("Salasanat eivät täsmää", category="error")
            return render_template("sign_up.html")
        if password1 == "":
            flash("Salasana ei voi olla tyhjä", category="error")
            return render_template("sign_up.html")
        if username == "":
            flash("Käyttäjänimi ei voi olla tyhjä", category="error")
            return render_template("sign_up.html")
        if users.register(username, password1):
            flash("Käyttäjä luotu!", category="success")
            return redirect("/")
        else:
            flash("Rekisteröinti epäonnistui, käyttäjänimi varattu", category="error")
        return render_template("sign_up.html")

@routes.route("/user_page", methods=["GET", "POST"])
def user_page():
    if request.method == "GET":
        """Connects to the next available port.
        Args:
            first_name = user[0]
            last_name = user[1]
            age = user[2]
            sex = user[3]
        """
        user = users.get_information()
        return render_template("user_page.html", user=user)


@routes.route("/user_page/delete", methods=["GET", "POST"])
def user_delete():
    if request.method == "GET":
        return render_template("delete_page.html")
    if request.method == "POST":
        if users.session["csrf_token"] != request.form["csrf_token"]:
            abort(403)
        deletion = request.form["deletion"]
        if deletion == "DELETE_INFO":
            users.delete_user_info()
            flash("Käyttäjätiedot poistettu", category="success")
            return redirect("/user_page")
        if deletion == "DELETE_RESULTS":
            users.delete_user_results()
            flash("Testihistoria poistettu", category="success")
            return redirect("/user_page")
        if deletion == "DELETE_USER":
            users.delete_user_results()
            users.delete_user()
            flash("Käyttäjä poistettu", category="success")
            users.logout()
            return redirect("/")
        else:
            return redirect("/user_page")


@routes.route("/user_page/update", methods=["GET", "POST"])
def update_user():
    if request.method == "GET":
        user = users.get_information()
        if user:
            return render_template("update_with_info.html", user=user)
        return render_template("update_without_info.html")
    if request.method == "POST":
        if users.session["csrf_token"] != request.form["csrf_token"]:
            abort(403)
        id_user = users.session["user_id"]
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        age = request.form["age"]
        sex = request.form["sex"]
        check_input = users.check_input(first_name, last_name, age, sex)
        if check_input != "All good everything":
            flash(check_input, category="error")
            return redirect("/user_page")
        if users.user_update(first_name, last_name, age, sex, id_user):
            flash("Tiedot tallennettu", category="success")
            return redirect("/user_page")
        else:
            flash("Tietojen tallennus epäonnistui", category="error")
    return redirect("/user_page")

@routes.route("/test_page", methods=["GET", "POST"])
def test_page():
    if request.method == "GET":
        user = users.get_information()
        if user:
            return render_template("tp_with_info.html", user=user)
        else:
            return render_template("tp_without_info.html")
    if request.method == "POST":
        test_data = request.form
        age = test_data["age"]
        sex = test_data["sex"]
        check_input = users.check_input("Some", "Randomstr", age, sex)
        if check_input != "All good everything":
            flash(check_input, category="error")
            return redirect("/test_page")
        fitness_levels = {}
        fitness_levels["saved"] = False
        for test, value in test_data.items():
            if "test" in test:
                if value != "":
                    results = tests.get_fitness_level(age, sex, test, value)
                    fitness_levels[test] = (value, results[0], results[1])
                else:
                    fitness_levels[test] = (0, 0, "ei tulosta")
        users.session["test_results"] = fitness_levels
        return redirect("/result_page")

@routes.route("/test_history", methods=["GET", "POST"])
def test_history():
    if request.method == "GET":
        history = users.get_result_history()
        if len(history) == 0:
            flash("Testihistoria on tyhjä", category="error")
            return redirect("/user_page")
        return render_template("test_history.html", len=len(history), history=history)
    if request.method == "POST":
        if users.session["csrf_token"] != request.form["csrf_token"]:
            abort(403)
        index = int(request.form["result_date"])
        history = users.get_result_history()
        results = users.get_user_result(history[index][0])
        if results:
            test_results = {}
            test_results["saved"] = True
            for item in results:
                test_results[item[0]] = (item[1], item[2], item[3])
            users.session["test_results"] = test_results
            return redirect("/result_page")
        else:
            flash("Testituloksen haku epäonnistui", category="error")
            return redirect("/user_page")

@routes.route("/result_page", methods=["GET", "POST"])
def result_page():
    if request.method == "GET":
        results = users.session["test_results"]
        if not results["saved"]:
            try:
                if users.session["user_id"]:
                    return render_template("result_page.html", results=results)
            except:
                pass
        return render_template("result_page_no_save.html", results=results)
    if request.method == "POST":
        save_status = request.form["save_status"]
        if save_status == "SAVE":
            if users.session["csrf_token"] != request.form["csrf_token"]:
                abort(403)
            if users.save_user_results():
                flash("Tulokset tallennettu", category="success")
            else:
                flash("Tulosten tallennuksessa tapahtui virhe", category="error")
        return redirect("/")