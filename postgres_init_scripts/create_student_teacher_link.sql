DROP TABLE IF EXISTS student_teacher_link CASCADE;

CREATE TABLE student_teacher_link (
    student_id INTEGER NOT NULL,
    teacher_id INTEGER NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(id),
    PRIMARY KEY (student_id, teacher_id)
);
