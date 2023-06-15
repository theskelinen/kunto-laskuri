from kuntolaskuri import db
from flask import session
from werkzeug.security import check_password_hash, generate_password_hash
import secrets
from sqlalchemy.sql import text

def login(username, password):
    sql = text("SELECT id, password, username FROM users WHERE username=:username")
    result = db.session.execute(sql, {"username":username})
    user = result.fetchone()
    if not user:
        return False
    else:
        if check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["user_name"] = user.username
            session["csrf_token"] = secrets.token_hex(16)
            return True
        else:
            return False

def logout():
    del session["user_id"]
    del session["user_name"]

def register(username, password):
    hash_value = generate_password_hash(password)
    try:
        sql = text("INSERT INTO users (username,password) VALUES (:username,:password)")
        db.session.execute(sql, {"username":username, "password":hash_value})
        db.session.commit()
    except:
        print("ei onnistu")
        return False
    return login(username, password)

def get_information():
    try:
        id_user = session["user_id"]
        sql = text("SELECT first_name, last_name, age, sex FROM user_info WHERE user_id=:id_user")
        result = db.session.execute(sql, {"id_user":id_user})
        user = result.fetchone()
        return user
    except:
        return False

def check_input(first_name, last_name, age, sex):
    if first_name == "":
        return "Etunimi on tyhjä, täytä kaikki lomakkeen kentät"
    if last_name == "":
        return "Sukunimi on tyhjä, täytä kaikki lomakkeen kentät"
    if age == "":
        return "Ikä on tyhjä, täytä kaikki lomakkeen kentät"
    try:
        age = int(age)
    except:
        return "Syötä ikä väliltä 18-70"
    if age not in range (18, 70):
        return "Syötä ikä väliltä 18-70"
    if sex == "":
        return "Sukupuoli on tyhjä, täytä kaikki lomakkeen kentät"
    if sex not in ["mies", "nainen", "muu"]:
        return "Syötä sukupuolen arvoksi mies, nainen tai muu"
    else:
        return "All good everything"


def user_update(first_name, last_name, age, sex, id_user):
    if get_information() == None:
        sql = text("INSERT INTO user_info (first_name, last_name, age, sex, user_id) VALUES (:first_name,:last_name,:age,:sex,:id_user)")
        db.session.execute(sql, {"first_name":first_name, "last_name":last_name, "age":age, "sex":sex, "id_user":id_user})
        db.session.commit()
        return True
    else:
        sql = text("UPDATE user_info SET first_name = :first_name, last_name = :last_name, age = :age, sex = :sex WHERE user_id = :id_user")
        db.session.execute(sql, {"first_name": first_name, "last_name": last_name, "age": age, "sex": sex, "id_user": id_user})
        db.session.commit()
        return True