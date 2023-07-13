from kuntolaskuri import db
from sqlalchemy.sql import text

def get_fitness_level(age, sex, test, value):
    if test == "nhs_liikkuvuus_testi" or test == "tasapainotesti":
        sql = text("SELECT fitness_level, meaning FROM balance_mobility WHERE test_name=:test AND min_req<=:value ORDER BY fitness_level DESC")
        result = db.session.execute(sql, {"test":test, "value":value})
        fitness_level = result.fetchone()
        return fitness_level
    else:
        if "nostotesti" in test:
            test = "nostotesti"
            if int(age) < 35:
                age = 35
        if test == "kyykistystesti" and int(age) < 20:
            age = 20
        if test == "istumaannousutesti" and int(age) < 25:
            age = 25
        sql = text("SELECT fitness_level, meaning FROM fitness_tests WHERE test_name=:test AND min_rep<=:value AND sex=:sex AND min_age<=:age ORDER BY fitness_level DESC")
        result = db.session.execute(sql, {"test":test, "value":value, "sex":sex, "age":age})
        fitness_level = result.fetchone()
        return fitness_level