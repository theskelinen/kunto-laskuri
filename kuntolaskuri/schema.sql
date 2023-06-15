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