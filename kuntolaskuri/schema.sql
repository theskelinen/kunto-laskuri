CREATE TABLE users (
    id SERIAL PRIMARY KEY, 
    username TEXT UNIQUE, 
    password TEXT
);
CREATE TABLE user_info (
    id SERIAL PRIMARY KEY, 
    first_name TEXT, 
    last_name TEXT, 
    age INTEGER, 
    sex TEXT, 
    user_id INTEGER REFERENCES users

);
CREATE TABLE user_results (
    id SERIAL PRIMARY KEY, 
    squat_reps INTEGER, 
    squat_fl  TEXT, 
    situp_reps INTEGER, 
    situp_fl  TEXT,
    ohpress_reps INTEGER, 
    ohpress_fl  TEXT,
    balance_time INTEGER, 
    balance_fl  TEXT,
    mobility_score INTEGER, 
    mobility_fl  TEXT,
    test_date DATE,
    user_id INTEGER REFERENCES users

);
Create TABLE fitness_tests (
    id SERIAL PRIMARY KEY,
    test_name TEXT,
    sex TEXT,
    min_age INTEGER,
    min_rep INTEGER,
    fitness_level INTEGER,
    meaning TEXT
);
Create TABLE balance_mobility (
    id SERIAL PRIMARY KEY,
    test_name TEXT,
    min_req INTEGER,
    fitness_level INTEGER,
    meaning TEXT
);

\COPY fitness_tests(test_name, sex, min_age, min_rep, fitness_level, meaning) FROM 'fitness_data.csv' DELIMITER ',' CSV HEADER;

\COPY balance_mobility(test_name, min_req, fitness_level, meaning) FROM 'balance_mobility.csv' DELIMITER ',' CSV HEADER;