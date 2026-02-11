CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY, 
    username TEXT UNIQUE, 
    password TEXT
);

CREATE TABLE IF NOT EXISTS user_info (
    id SERIAL PRIMARY KEY, 
    first_name TEXT, 
    last_name TEXT, 
    age INTEGER, 
    sex TEXT, 
    user_id INTEGER REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS user_results (
    id SERIAL PRIMARY KEY, 
    test_name TEXT, 
    test_reps INTEGER, 
    test_fl INTEGER, 
    test_fl_meaning TEXT, 
    test_time TIMESTAMP,
    user_id INTEGER REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS fitness_tests (
    id SERIAL PRIMARY KEY,
    test_name TEXT,
    sex TEXT,
    min_age INTEGER,
    min_rep INTEGER,
    fitness_level INTEGER,
    meaning TEXT
);

CREATE TABLE IF NOT EXISTS balance_mobility (
    id SERIAL PRIMARY KEY,
    test_name TEXT,
    min_req INTEGER,
    fitness_level INTEGER,
    meaning TEXT
);

-- Lataa CSV-data (toimii vain jos tiedostot ovat oikeassa polussa)
\COPY fitness_tests(test_name, sex, min_age, min_rep, fitness_level, meaning) FROM '/docker-entrypoint-initdb.d/fitness_data.csv' DELIMITER ',' CSV HEADER;

\COPY balance_mobility(test_name, min_req, fitness_level, meaning) FROM '/docker-entrypoint-initdb.d/balance_mobility.csv' DELIMITER ',' CSV HEADER;