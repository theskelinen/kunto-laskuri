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