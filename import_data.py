import csv
import sqlite3

DATABASE = "students.db"
CSV_FILE = "college_student_management_dataset.csv"


def import_students():
    connection = sqlite3.connect(DATABASE)

    with open(CSV_FILE, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        count = 0

        for row in reader:
            connection.execute("""
                INSERT OR REPLACE INTO students (
                    student_id,
                    age,
                    gender,
                    major,
                    GPA,
                    course_load,
                    avg_course_grade,
                    attendance_rate,
                    enrollment_status,
                    lms_logins_past_month,
                    avg_session_duration_minutes,
                    assignment_submission_rate,
                    forum_participation_count,
                    video_completion_rate,
                    risk_level
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["student_id"],
                row["age"],
                row["gender"],
                row["major"],
                row["GPA"],
                row["course_load"],
                row["avg_course_grade"],
                row["attendance_rate"],
                row["enrollment_status"],
                row["lms_logins_past_month"],
                row["avg_session_duration_minutes"],
                row["assignment_submission_rate"],
                row["forum_participation_count"],
                row["video_completion_rate"],
                row["risk_level"]
            ))

            count += 1

    connection.commit()
    connection.close()

    print(f"Student data imported successfully! {count} students imported.")


if __name__ == "__main__":
    import_students()