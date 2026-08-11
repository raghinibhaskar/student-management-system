import sqlite3

DATABASE = "students.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            age INTEGER,
            gender TEXT,
            major TEXT,
            GPA REAL,
            course_load INTEGER,
            avg_course_grade REAL,
            attendance_rate REAL,
            enrollment_status TEXT,
            lms_logins_past_month INTEGER,
            avg_session_duration_minutes INTEGER,
            assignment_submission_rate REAL,
            forum_participation_count INTEGER,
            video_completion_rate REAL,
            risk_level TEXT
        )
    """)

    connection.commit()
    connection.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")