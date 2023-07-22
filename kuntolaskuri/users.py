from kuntolaskuri import db
from flask import session
from werkzeug.security import check_password_hash, generate_password_hash
import secrets
from datetime import datetime
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
            session["test_results"] = "This will store the user's test results"
            return True
        else:
            return False

def logout():
    del session["user_id"]
    del session["user_name"]
    del session["csrf_token"]
    del session["test_results"]

def register(username, password):
    hash_value = generate_password_hash(password)
    try:
        sql = text("INSERT INTO users (username,password) VALUES (:username,:password)")
        db.session.execute(sql, {"username":username, "password":hash_value})
        db.session.commit()
    except:
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
    if age not in range (18, 71):
        return "Syötä ikä väliltä 18-70"
    if sex == "":
        return "Sukupuoli on tyhjä, täytä kaikki lomakkeen kentät"
    if sex not in ["mies", "nainen"]:
        return "Syötä sukupuolen arvoksi mies tai nainen"
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

def delete_user_info():
    id_user = session["user_id"]
    sql = text("DELETE FROM user_info WHERE user_id=:id_user;")
    db.session.execute(sql, {"id_user":id_user})
    db.session.commit()
    return True

def delete_user():
    id_user = session["user_id"]
    sql = text("DELETE FROM users WHERE id=:id_user;")
    db.session.execute(sql, {"id_user":id_user})
    db.session.commit()
    return True

def delete_user_results():
    id_user = session["user_id"]
    sql = text("DELETE FROM user_results WHERE user_id=:id_user;")
    db.session.execute(sql, {"id_user":id_user})
    db.session.commit()
    return True

def save_user_results():
    now = datetime.now()
    id_user = session["user_id"]
    test_results = session["test_results"]
    for test in test_results:
        if "testi" in test:
            test_name = test
            test_reps = test_results[test][0]
            test_fl = test_results[test][1]
            test_fl_meaning = test_results[test][2]
            sql = text("INSERT INTO user_results (test_name, test_reps, test_fl, test_fl_meaning, test_time, user_id) VALUES (:test_name,:test_reps,:test_fl,:test_fl_meaning,:test_time,:id_user)")
            db.session.execute(sql, {"test_name":test_name,"test_reps":test_reps,"test_fl":test_fl,"test_fl_meaning":test_fl_meaning,"test_time":now,"id_user":id_user})
    db.session.commit()
    return True

def get_result_history():
    id_user = session["user_id"]
    sql = text("SELECT test_time FROM user_results WHERE user_id=:id_user ORDER BY test_time DESC")
    result = db.session.execute(sql, {"id_user":id_user})
    history = result.fetchall()
    duplicates_removed = []
    [duplicates_removed.append(test_time) for test_time in history if test_time not in duplicates_removed]
    return duplicates_removed

def get_user_result(result_date):
        id_user = session["user_id"]
        sql = text("SELECT test_name, test_reps, test_fl, test_fl_meaning FROM user_results WHERE user_id=:id_user AND test_time=:test_time")
        result = db.session.execute(sql, {"id_user":id_user, "test_time":result_date})
        test_results = result.fetchall()
        if not test_results:
            return False
        return test_results