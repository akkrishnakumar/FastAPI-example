DROP TABLE IF EXISTS students CASCADE;

-- Create the students table.
CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);