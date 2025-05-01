from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import psycopg2
import logging
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

DATABASE_URL = "postgresql://mydatabaseuser:password@localhost:5432/postgres"  # Replace with your actual details

class StudentIn(BaseModel):
    name: str
    id: int

class StudentOut(BaseModel):
    name: str
    id: int
    teachers: List[str] 

class TeacherIn(BaseModel):
    name: str
    id: int

class TeacherOut(BaseModel):
    name: str
    id: int
    students: List[str]

class StudentTeacherLink(BaseModel):
    student_id: int
    teacher_id: int

def get_db():
    conn = None
    try:
        logger.info("Connecting to the database...")
        conn = psycopg2.connect(DATABASE_URL)
        yield conn
    except psycopg2.Error as e:
        logger.error(f"Error connecting to the database: {e}")
        raise HTTPException(status_code=500, detail=f"Could not connect to the database: {e}")
    finally:
        if conn:
            logger.info("Closing the database connection...")
            conn.close()

# Modified dependency to yield the connection directly
async def get_db_dependency():
    conn = None
    try:
        logger.info("Connecting to the database for the request...")
        conn = psycopg2.connect(DATABASE_URL)
        yield conn
    except psycopg2.Error as e:
        logger.error(f"Error connecting to the database in dependency: {e}")
        raise HTTPException(status_code=500, detail=f"Could not connect to the database: {e}")
    finally:
        if conn:
            logger.info("Closing the database connection after the request...")
            conn.close()
            
@app.get("/ping_db", status_code=200)
async def ping_database(db: psycopg2.extensions.connection = Depends(get_db)):
    try:
        cursor = db.cursor()
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()
        if result == (1,):
            return {"message": "PostgreSQL is reachable!"}
        else:
            logger.warning("Ping query returned unexpected result.")
            raise HTTPException(status_code=500, detail="Unexpected response from database ping")
    except psycopg2.Error as e:
        logger.error(f"Error during database ping: {e}")
        raise HTTPException(status_code=500, detail=f"Error pinging the database: {e}")

@app.post("/students/", status_code=201)
async def create_student(student: StudentIn, db: psycopg2.extensions.connection = Depends(get_db_dependency)):
    try:
        cursor = db.cursor()
        query = "INSERT INTO students (name, id) VALUES (%s, %s)"
        cursor.execute(query, (student.name, student.id))
        db.commit()
        return Response(status_code=201)
    except psycopg2.Error as e:
        db.rollback()  # Rollback changes on error
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.get("/students/{student_id}", response_model=StudentOut)
async def get_student(student_id: int):
    try:
        with get_db() as db:
            cursor = db.cursor()
            query = "SELECT name, id FROM students WHERE id = %s"
            cursor.execute(query, (student_id,))
            result = cursor.fetchone()
            if result:
                return StudentOut(name=result[0], id=result[1])
            else:
                raise HTTPException(status_code=404, detail="Student not found")
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@app.get("/students/", response_model=List[StudentOut])  # New endpoint for getting all students
async def get_all_students(db: psycopg2.extensions.connection = Depends(get_db_dependency)):
    try:
        cursor = db.cursor()
        query = query = """
            SELECT s.name, s.id, t.name as teacher_name
            FROM students s
            LEFT JOIN student_teacher_link st ON s.id = st.student_id
            LEFT JOIN teachers t ON st.teacher_id = t.id
            ORDER BY s.id
        """
        cursor.execute(query)
        results = cursor.fetchall()
        students = {}
        for row in results:
            student_id = row[1]
            if student_id not in students:
                students[student_id] = {
                    "name": row[0],
                    "id": student_id,
                    "teachers": []
                }
            if row[2]:
                students[student_id]["teachers"].append(row[2])

        return [StudentOut(**student) for student in students.values()]
    except psycopg2.Error as e:
        logger.error(f"Database error during retrieval of all students: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    
@app.post("/teachers/", response_model=TeacherOut, status_code=201)
async def create_teacher(teacher: TeacherIn, db: psycopg2.extensions.connection = Depends(get_db_dependency)):
    try:
        cursor = db.cursor()
        query = "INSERT INTO teachers (name, id) VALUES (%s, %s)"
        cursor.execute(query, (teacher.name, teacher.id))
        db.commit()
        return TeacherOut(**teacher.model_dump())
    except psycopg2.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.get("/teachers/{teacher_id}", response_model=TeacherOut)
async def get_teacher(teacher_id: int, db: psycopg2.extensions.connection = Depends(get_db_dependency)):
    try:
        cursor = db.cursor()
        query = "SELECT name, id FROM teachers WHERE id = %s"
        cursor.execute(query, (teacher_id,))
        result = cursor.fetchone()
        if result:
            return TeacherOut(name=result[0], id=result[1])
        else:
            raise HTTPException(status_code=404, detail="Teacher not found")
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.get("/teachers/", response_model=List[TeacherOut])
async def get_all_teachers(db: psycopg2.extensions.connection = Depends(get_db_dependency)):
    try:
        cursor = db.cursor()
        query = """
            SELECT t.name, t.id, s.name as student_name
            FROM teachers t
            LEFT JOIN student_teacher_link st ON t.id = st.teacher_id
            LEFT JOIN students s ON st.student_id = s.id
            ORDER BY t.id
            """
        cursor.execute(query)
        results = cursor.fetchall()
        teachers = {}
        for row in results:
            teacher_id = row[1]
            if teacher_id not in teachers:
                teachers[teacher_id] = {
                    "name": row[0],
                    "id": teacher_id,
                    "students": []
                }
            if row[2]:
                teachers[teacher_id]["students"].append(row[2])
        return [TeacherOut(**teacher) for teacher in teachers.values()]
    except psycopg2.Error as e:
        logger.error(f"Database error during retrieval of all teachers: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.post("/student/teacher/", status_code=204)
async def add_teacher_to_student(
    link: StudentTeacherLink,
    db: psycopg2.extensions.connection = Depends(get_db_dependency),
):
    """
    Links a teacher to a student, given the teacher's ID.

    Args:
        link (StudentTeacherLink): An object containing student_id and teacher_id.

    Raises:
        HTTPException (404): If the student or teacher is not found.
        HTTPException (500): For database errors.
    """
    try:
        cursor = db.cursor()
        student_id = link.student_id
        teacher_id = link.teacher_id
        # check if student exists
        cursor.execute("SELECT id FROM students WHERE id = %s", (student_id,))
        student_exists = cursor.fetchone()
        if not student_exists:
            raise HTTPException(
                status_code=404, detail=f"Student with id {student_id} not found"
            )

        # check if teacher exists
        cursor.execute("SELECT id FROM teachers WHERE id = %s", (teacher_id,))
        teacher_exists = cursor.fetchone()
        if not teacher_exists:
            raise HTTPException(
                status_code=404, detail=f"Teacher with id {teacher_id} not found"
            )

        # Check if the link already exists
        cursor.execute(
            "SELECT student_id, teacher_id FROM student_teacher_link WHERE student_id = %s AND teacher_id = %s",
            (student_id, teacher_id),
        )
        existing_link = cursor.fetchone()
        if existing_link:
            return  # No need to create the link again

        query = "INSERT INTO student_teacher_link (student_id, teacher_id) VALUES (%s, %s)"
        cursor.execute(query, (student_id, teacher_id))
        db.commit()
    except psycopg2.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.get("/healthcheck", status_code=200)
async def healthcheck():
    return "It works !!!!"