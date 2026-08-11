from flask import (
    Flask,
    render_template,
    render_template_string,
    request,
    redirect,
    url_for,
    session,
    Response,
    flash
)

from database import init_db, get_db_connection

import csv
from io import StringIO


app = Flask(__name__)

# ============================================================
# APPLICATION SETTINGS
# ============================================================

app.secret_key = "studentpulse-secret-key"

# Login credentials
USERNAME = "admin"
PASSWORD = "studentpulse123"

# Initialize database
init_db()


# ============================================================
# LOGIN REQUIRED DECORATOR
# ============================================================

from functools import wraps


def login_required(route_function):

    @wraps(route_function)
    def wrapper(*args, **kwargs):

        if "logged_in" not in session:

            flash(
                "Please login to access StudentPulse.",
                "error"
            )

            return redirect(
                url_for("login")
            )

        return route_function(
            *args,
            **kwargs
        )

    return wrapper


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=[
        "GET",
        "POST"
    ]
)
def login():

    # Always show the login page when the application is opened.
    # An old browser session will not skip the login screen.

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        if (
            username == USERNAME
            and password == PASSWORD
        ):

            # Clear any old session data and create a fresh session.
            session.clear()

            session["logged_in"] = True
            session["username"] = username

            flash(
                "Login successful! Welcome to StudentPulse.",
                "success"
            )

            return redirect(
                url_for("dashboard")
            )

        else:

            flash(
                "Invalid username or password.",
                "error"
            )

    return render_template(
        "login.html"
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route(
    "/logout",
    methods=[
        "GET",
        "POST"
    ]
)
def logout():

    # GET shows a confirmation screen.
    if request.method == "GET":

        return render_template_string(
            """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport"
                      content="width=device-width, initial-scale=1.0">
                <title>Confirm Logout | StudentPulse</title>

                <style>
                    * {
                        box-sizing: border-box;
                    }

                    body {
                        margin: 0;
                        min-height: 100vh;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        font-family: Arial, Helvetica, sans-serif;
                        background: #f5f6fa;
                    }

                    .logout-card {
                        width: 420px;
                        max-width: calc(100% - 40px);
                        background: #ffffff;
                        padding: 42px 38px;
                        border: 4px solid #222;
                        border-radius: 14px;
                        box-shadow: 10px 10px 0 #222;
                        text-align: center;
                    }

                    .logout-icon {
                        width: 64px;
                        height: 64px;
                        margin: 0 auto 20px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        border-radius: 50%;
                        background: #f1f1f1;
                        font-size: 30px;
                    }

                    h1 {
                        margin: 0 0 10px;
                        font-size: 28px;
                        color: #222;
                    }

                    p {
                        margin: 0 0 30px;
                        color: #777;
                        font-size: 15px;
                        line-height: 1.5;
                    }

                    .actions {
                        display: flex;
                        gap: 12px;
                    }

                    .actions form,
                    .actions a {
                        flex: 1;
                    }

                    button,
                    .cancel-button {
                        width: 100%;
                        padding: 13px 16px;
                        border-radius: 7px;
                        font-size: 15px;
                        font-weight: 700;
                        cursor: pointer;
                        text-decoration: none;
                        display: inline-flex;
                        align-items: center;
                        justify-content: center;
                    }

                    .logout-button {
                        border: 2px solid #222;
                        background: #222;
                        color: #fff;
                    }

                    .logout-button:hover {
                        background: #444;
                    }

                    .cancel-button {
                        border: 2px solid #ddd;
                        background: #fff;
                        color: #333;
                    }

                    .cancel-button:hover {
                        background: #f5f5f5;
                    }

                    @media (max-width: 500px) {
                        .logout-card {
                            padding: 34px 24px;
                            box-shadow: 7px 7px 0 #222;
                        }

                        .actions {
                            flex-direction: column-reverse;
                        }
                    }
                </style>
            </head>

            <body>
                <div class="logout-card">

                    <div class="logout-icon">↪</div>

                    <h1>Log out?</h1>

                    <p>
                        Are you sure you want to log out of
                        StudentPulse?
                    </p>

                    <div class="actions">

                        <a
                            href="{{ url_for('dashboard') }}"
                            class="cancel-button"
                        >
                            Cancel
                        </a>

                        <form
                            method="POST"
                            action="{{ url_for('logout') }}"
                        >
                            <button
                                type="submit"
                                class="logout-button"
                            >
                                Yes, Log Out
                            </button>
                        </form>

                    </div>

                </div>
            </body>
            </html>
            """
        )

    # POST actually logs the user out.
    session.clear()

    flash(
        "You have been logged out successfully.",
        "success"
    )

    return redirect(
        url_for("login")
    )


# ============================================================
# HELPER FUNCTION - VALIDATE STEP 1 STUDENT DATA
# ============================================================

def validate_student_data(data):

    errors = []


    required_fields = [

        "student_id",

        "age",

        "gender",

        "major",

        "GPA",

        "course_load",

        "avg_course_grade",

        "attendance_rate"

    ]


    # Check required fields

    for field in required_fields:

        value = data.get(
            field,
            ""
        ).strip()


        if not value:

            errors.append(

                f"{field.replace('_', ' ').title()} is required."

            )


    # Stop here if required fields are missing

    if errors:

        return errors


    # --------------------------------------------------------
    # Student ID
    # --------------------------------------------------------

    if len(
        data["student_id"].strip()
    ) < 2:

        errors.append(

            "Student ID must contain at least 2 characters."

        )


    # --------------------------------------------------------
    # Age
    # --------------------------------------------------------

    try:

        age = int(
            data["age"]
        )


        if age < 1 or age > 100:

            errors.append(

                "Age must be between 1 and 100."

            )

    except ValueError:

        errors.append(

            "Age must be a valid whole number."

        )


    # --------------------------------------------------------
    # GPA
    # --------------------------------------------------------

    try:

        gpa = float(
            data["GPA"]
        )


        if gpa < 0 or gpa > 10:

            errors.append(

                "GPA must be between 0 and 10."

            )

    except ValueError:

        errors.append(

            "GPA must be a valid number."

        )


    # --------------------------------------------------------
    # Course Load
    # --------------------------------------------------------

    try:

        course_load = int(
            data["course_load"]
        )


        if course_load < 1:

            errors.append(

                "Course load must be at least 1."

            )

    except ValueError:

        errors.append(

            "Course load must be a valid whole number."

        )


    # --------------------------------------------------------
    # Average Course Grade
    # --------------------------------------------------------

    try:

        avg_course_grade = float(
            data["avg_course_grade"]
        )


        if (

            avg_course_grade < 0

            or avg_course_grade > 100

        ):

            errors.append(

                "Average course grade must be between 0 and 100."

            )

    except ValueError:

        errors.append(

            "Average course grade must be a valid number."

        )


    # --------------------------------------------------------
    # Attendance Rate
    # Database stores this as decimal.
    # Example: 0.85 = 85%
    # --------------------------------------------------------

    try:

        attendance = float(
            data["attendance_rate"]
        )


        if (

            attendance < 0

            or attendance > 1

        ):

            errors.append(

                "Attendance rate must be between 0 and 1."

            )

    except ValueError:

        errors.append(

            "Attendance rate must be a valid decimal between 0 and 1."

        )


    return errors

@app.route("/")
def home():
    return redirect(url_for("login"))


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
@login_required
def dashboard():
    connection = get_db_connection()


    total_students = connection.execute(

        "SELECT COUNT(*) FROM students"

    ).fetchone()[0]


    average_gpa = connection.execute(

        "SELECT AVG(GPA) FROM students"

    ).fetchone()[0]


    average_attendance = connection.execute(

        "SELECT AVG(attendance_rate) FROM students"

    ).fetchone()[0]


    high_risk_students = connection.execute(

        """

        SELECT COUNT(*)

        FROM students

        WHERE risk_level = 'High'

        """

    ).fetchone()[0]


    medium_risk_students = connection.execute(

        """

        SELECT COUNT(*)

        FROM students

        WHERE risk_level = 'Medium'

        """

    ).fetchone()[0]


    low_risk_students = connection.execute(

        """

        SELECT COUNT(*)

        FROM students

        WHERE risk_level = 'Low'

        """

    ).fetchone()[0]


    risk_distribution = {

        "High":
            high_risk_students,

        "Medium":
            medium_risk_students,

        "Low":
            low_risk_students

    }


    # --------------------------------------------------------
    # Attendance Distribution
    # --------------------------------------------------------

    attendance_below_50 = connection.execute(

        """

        SELECT COUNT(*)

        FROM students

        WHERE attendance_rate < 0.50

        """

    ).fetchone()[0]


    attendance_50_to_70 = connection.execute(

        """

        SELECT COUNT(*)

        FROM students

        WHERE attendance_rate >= 0.50

        AND attendance_rate < 0.70

        """

    ).fetchone()[0]


    attendance_above_70 = connection.execute(

        """

        SELECT COUNT(*)

        FROM students

        WHERE attendance_rate >= 0.70

        """

    ).fetchone()[0]


    attendance_distribution = {

        "Below 50%":
            attendance_below_50,

        "50% - 69%":
            attendance_50_to_70,

        "70% and Above":
            attendance_above_70

    }


    # --------------------------------------------------------
    # Major Distribution
    # --------------------------------------------------------

    major_data = connection.execute(

        """

        SELECT

            major,

            COUNT(*) AS student_count

        FROM students

        GROUP BY major

        ORDER BY student_count DESC

        """

    ).fetchall()


    major_names = []

    major_counts = []


    for row in major_data:

        major_names.append(

            row["major"]

        )


        major_counts.append(

            row["student_count"]

        )


    # --------------------------------------------------------
    # Average Performance
    # --------------------------------------------------------

    average_course_grade = connection.execute(

        """

        SELECT AVG(avg_course_grade)

        FROM students

        """

    ).fetchone()[0]


    average_assignment_rate = connection.execute(

        """

        SELECT AVG(assignment_submission_rate)

        FROM students

        """

    ).fetchone()[0]


    average_video_completion = connection.execute(

        """

        SELECT AVG(video_completion_rate)

        FROM students

        """

    ).fetchone()[0]


    connection.close()


    return render_template(

        "dashboard.html",

        total_students=
            total_students,

        average_gpa=
            average_gpa or 0,

        average_attendance=
            average_attendance or 0,

        high_risk_students=
            high_risk_students,

        medium_risk_students=
            medium_risk_students,

        low_risk_students=
            low_risk_students,

        risk_distribution=
            risk_distribution,

        attendance_below_50=
            attendance_below_50,

        attendance_50_to_70=
            attendance_50_to_70,

        attendance_above_70=
            attendance_above_70,

        attendance_distribution=
            attendance_distribution,

        major_names=
            major_names,

        major_counts=
            major_counts,

        average_course_grade=
            average_course_grade or 0,

        average_assignment_rate=
            average_assignment_rate or 0,

        average_video_completion=
            average_video_completion or 0

    )


# ============================================================
# STUDENT RECORDS
# ============================================================

@app.route(
    "/students"
)
@login_required
def students():

    connection = get_db_connection()


    search = request.args.get(
        "search",
        ""
    )


    major = request.args.get(
        "major",
        ""
    )


    risk = request.args.get(
        "risk",
        ""
    )


    status = request.args.get(
        "status",
        ""
    )


    query = """

        SELECT *

        FROM students

        WHERE 1=1

    """


    parameters = []


    # Search by Student ID

    if search:

        query += """

            AND student_id LIKE ?

        """


        parameters.append(

            f"%{search}%"

        )


    # Filter by Major

    if major:

        query += """

            AND major = ?

        """


        parameters.append(

            major

        )


    # Filter by Risk

    if risk:

        query += """

            AND risk_level = ?

        """


        parameters.append(

            risk

        )


    # Filter by Status

    if status:

        query += """

            AND enrollment_status = ?

        """


        parameters.append(

            status

        )


    student_list = connection.execute(

        query,

        parameters

    ).fetchall()


    # Get Majors

    majors = connection.execute(

        """

        SELECT DISTINCT major

        FROM students

        ORDER BY major

        """

    ).fetchall()


    # Get Enrollment Statuses

    statuses = connection.execute(

        """

        SELECT DISTINCT enrollment_status

        FROM students

        ORDER BY enrollment_status

        """

    ).fetchall()


    connection.close()


    return render_template(

        "students.html",

        students=
            student_list,

        majors=
            majors,

        statuses=
            statuses,

        search=
            search,

        selected_major=
            major,

        selected_risk=
            risk,

        selected_status=
            status

    )


# ============================================================
# VIEW INDIVIDUAL STUDENT
# ============================================================

@app.route(
    "/student/<student_id>"
)
@login_required
def student_details(
    student_id
):

    connection = get_db_connection()


    student = connection.execute(

        """

        SELECT *

        FROM students

        WHERE student_id = ?

        """,

        (

            student_id,

        )

    ).fetchone()


    connection.close()


    if student is None:

        flash(

            "Student not found.",

            "error"

        )


        return redirect(

            url_for(

                "students"

            )

        )


    return render_template(

        "student_details.html",

        student=
            student

    )


# ============================================================
# EDIT STUDENT
# ============================================================

@app.route(
    "/edit/<student_id>",
    methods=[
        "GET",
        "POST"
    ]
)
@login_required
def edit_student(
    student_id
):

    connection = get_db_connection()


    student = connection.execute(

        """

        SELECT *

        FROM students

        WHERE student_id = ?

        """,

        (

            student_id,

        )

    ).fetchone()


    if student is None:

        connection.close()


        flash(

            "Student not found.",

            "error"

        )


        return redirect(

            url_for(

                "students"

            )

        )


    if request.method == "POST":


        data = {

            "student_id":
                student_id,

            "age":
                request.form.get(
                    "age",
                    ""
                ),

            "gender":
                request.form.get(
                    "gender",
                    ""
                ),

            "major":
                request.form.get(
                    "major",
                    ""
                ),

            "GPA":
                request.form.get(
                    "GPA",
                    ""
                ),

            "course_load":
                request.form.get(
                    "course_load",
                    ""
                ),

            "avg_course_grade":
                request.form.get(
                    "avg_course_grade",
                    ""
                ),

            "attendance_rate":
                request.form.get(
                    "attendance_rate",
                    ""
                )

        }


        errors = validate_student_data(

            data

        )


        if errors:

            connection.close()


            for error in errors:

                flash(

                    error,

                    "error"

                )


            return render_template(

                "edit_student.html",

                student=
                    student

            )


        # ----------------------------------------------------
        # Validate Step 2 fields
        # ----------------------------------------------------

        step2_errors = []


        enrollment_status = request.form.get(

            "enrollment_status",

            ""

        )


        lms_logins = request.form.get(

            "lms_logins_past_month",

            ""

        )


        avg_session = request.form.get(

            "avg_session_duration_minutes",

            ""

        )


        assignment_rate = request.form.get(

            "assignment_submission_rate",

            ""

        )


        forum_count = request.form.get(

            "forum_participation_count",

            ""

        )


        video_completion = request.form.get(

            "video_completion_rate",

            ""

        )


        risk_level = request.form.get(

            "risk_level",

            ""

        )


        if not enrollment_status.strip():

            step2_errors.append(

                "Enrollment status is required."

            )


        try:

            if int(lms_logins) < 0:

                step2_errors.append(

                    "LMS logins cannot be negative."

                )

        except ValueError:

            step2_errors.append(

                "LMS logins must be a valid number."

            )


        try:

            if int(avg_session) < 0:

                step2_errors.append(

                    "Session duration cannot be negative."

                )

        except ValueError:

            step2_errors.append(

                "Session duration must be a valid number."

            )


        try:

            if (

                float(assignment_rate) < 0

                or float(assignment_rate) > 1

            ):

                step2_errors.append(

                    "Assignment submission rate must be between 0 and 1."

                )

        except ValueError:

            step2_errors.append(

                "Assignment submission rate must be a valid decimal between 0 and 1."

            )


        try:

            if int(forum_count) < 0:

                step2_errors.append(

                    "Forum participation count cannot be negative."

                )

        except ValueError:

            step2_errors.append(

                "Forum participation count must be a valid number."

            )


        try:

            if (

                float(video_completion) < 0

                or float(video_completion) > 1

            ):

                step2_errors.append(

                    "Video completion rate must be between 0 and 1."

                )

        except ValueError:

            step2_errors.append(

                "Video completion rate must be a valid decimal between 0 and 1."

            )


        if not risk_level.strip():

            step2_errors.append(

                "Risk level is required."

            )


        if step2_errors:

            connection.close()


            for error in step2_errors:

                flash(

                    error,

                    "error"

                )


            return render_template(

                "edit_student.html",

                student=
                    student

            )


        # ----------------------------------------------------
        # Update Student
        # ----------------------------------------------------

        connection.execute(

            """

            UPDATE students

            SET

                age = ?,

                gender = ?,

                major = ?,

                GPA = ?,

                course_load = ?,

                avg_course_grade = ?,

                attendance_rate = ?,

                enrollment_status = ?,

                lms_logins_past_month = ?,

                avg_session_duration_minutes = ?,

                assignment_submission_rate = ?,

                forum_participation_count = ?,

                video_completion_rate = ?,

                risk_level = ?

            WHERE student_id = ?

            """,

            (

                data["age"],

                data["gender"],

                data["major"],

                data["GPA"],

                data["course_load"],

                data["avg_course_grade"],

                data["attendance_rate"],

                enrollment_status,

                lms_logins,

                avg_session,

                assignment_rate,

                forum_count,

                video_completion,

                risk_level,

                student_id

            )

        )


        connection.commit()

        connection.close()


        flash(

            "Student updated successfully!",

            "success"

        )


        return redirect(

            url_for(

                "student_details",

                student_id=
                    student_id

            )

        )


    connection.close()


    return render_template(

        "edit_student.html",

        student=
            student

    )


# ============================================================
# DELETE STUDENT
# ============================================================

@app.route(
    "/delete/<student_id>",
    methods=[
        "POST"
    ]
)
@login_required
def delete_student(
    student_id
):

    connection = get_db_connection()


    connection.execute(

        """

        DELETE FROM students

        WHERE student_id = ?

        """,

        (

            student_id,

        )

    )


    connection.commit()

    connection.close()


    flash(

        "Student deleted successfully!",

        "success"

    )


    return redirect(

        url_for(

            "students"

        )

    )


# ============================================================
# ADD STUDENT - STEP 1
# ============================================================

@app.route(
    "/add",
    methods=[
        "GET",
        "POST"
    ]
)
@login_required
def add_student():

    if request.method == "POST":


        data = {

            "student_id":
                request.form.get(
                    "student_id",
                    ""
                ),

            "age":
                request.form.get(
                    "age",
                    ""
                ),

            "gender":
                request.form.get(
                    "gender",
                    ""
                ),

            "major":
                request.form.get(
                    "major",
                    ""
                ),

            "GPA":
                request.form.get(
                    "GPA",
                    ""
                ),

            "course_load":
                request.form.get(
                    "course_load",
                    ""
                ),

            "avg_course_grade":
                request.form.get(
                    "avg_course_grade",
                    ""
                ),

            "attendance_rate":
                request.form.get(
                    "attendance_rate",
                    ""
                )

        }


        # Validate Step 1

        errors = validate_student_data(

            data

        )


        # Check duplicate Student ID

        if not errors:

            connection = get_db_connection()


            existing_student = connection.execute(

                """

                SELECT student_id

                FROM students

                WHERE student_id = ?

                """,

                (

                    data["student_id"],

                )

            ).fetchone()


            connection.close()


            if existing_student:

                errors.append(

                    "Student ID already exists. Please use a different Student ID."

                )


        # Display errors

        if errors:

            for error in errors:

                flash(

                    error,

                    "error"

                )


            return render_template(

                "add_student.html"

            )


        # Store validated data

        session[

            "student_data"

        ] = data


        return redirect(

            url_for(

                "add_student_step2"

            )

        )


    return render_template(

        "add_student.html"

    )


# ============================================================
# ADD STUDENT - STEP 2
# ============================================================

@app.route(
    "/add/step2",
    methods=[
        "GET",
        "POST"
    ]
)
@login_required
def add_student_step2():


    if (

        "student_data"

        not in session

    ):

        return redirect(

            url_for(

                "add_student"

            )

        )


    if request.method == "POST":


        student_data = session[

            "student_data"

        ]


        # Get Step 2 fields

        enrollment_status = request.form.get(

            "enrollment_status",

            ""

        )


        lms_logins = request.form.get(

            "lms_logins_past_month",

            ""

        )


        avg_session = request.form.get(

            "avg_session_duration_minutes",

            ""

        )


        assignment_rate = request.form.get(

            "assignment_submission_rate",

            ""

        )


        forum_count = request.form.get(

            "forum_participation_count",

            ""

        )


        video_completion = request.form.get(

            "video_completion_rate",

            ""

        )


        risk_level = request.form.get(

            "risk_level",

            ""

        )


        step2_errors = []


        # ----------------------------------------------------
        # Enrollment Status
        # ----------------------------------------------------

        if not enrollment_status.strip():

            step2_errors.append(

                "Enrollment status is required."

            )


        # ----------------------------------------------------
        # LMS Logins
        # ----------------------------------------------------

        try:

            if int(lms_logins) < 0:

                step2_errors.append(

                    "LMS logins cannot be negative."

                )

        except ValueError:

            step2_errors.append(

                "LMS logins must be a valid whole number."

            )


        # ----------------------------------------------------
        # Average Session Duration
        # ----------------------------------------------------

        try:

            if int(avg_session) < 0:

                step2_errors.append(

                    "Session duration cannot be negative."

                )

        except ValueError:

            step2_errors.append(

                "Session duration must be a valid whole number."

            )


        # ----------------------------------------------------
        # Assignment Submission Rate
        # Stored as decimal 0-1
        # ----------------------------------------------------

        try:

            assignment_value = float(

                assignment_rate

            )


            if (

                assignment_value < 0

                or assignment_value > 1

            ):

                step2_errors.append(

                    "Assignment submission rate must be between 0 and 1."

                )

        except ValueError:

            step2_errors.append(

                "Assignment submission rate must be a valid decimal between 0 and 1."

            )


        # ----------------------------------------------------
        # Forum Participation
        # ----------------------------------------------------

        try:

            if int(forum_count) < 0:

                step2_errors.append(

                    "Forum participation count cannot be negative."

                )

        except ValueError:

            step2_errors.append(

                "Forum participation count must be a valid whole number."

            )


        # ----------------------------------------------------
        # Video Completion Rate
        # Stored as decimal 0-1
        # ----------------------------------------------------

        try:

            video_value = float(

                video_completion

            )


            if (

                video_value < 0

                or video_value > 1

            ):

                step2_errors.append(

                    "Video completion rate must be between 0 and 1."

                )

        except ValueError:

            step2_errors.append(

                "Video completion rate must be a valid decimal between 0 and 1."

            )


        # ----------------------------------------------------
        # Risk Level
        # ----------------------------------------------------

        if not risk_level.strip():

            step2_errors.append(

                "Risk level is required."

            )


        # ----------------------------------------------------
        # Display Errors
        # ----------------------------------------------------

        if step2_errors:

            for error in step2_errors:

                flash(

                    error,

                    "error"

                )


            return render_template(

                "add_student_step2.html"

            )


        # ----------------------------------------------------
        # Insert Student
        # ----------------------------------------------------

        connection = get_db_connection()


        try:

            connection.execute(

                """

                INSERT INTO students (

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

                VALUES (

                    ?, ?, ?, ?, ?,

                    ?, ?, ?, ?, ?,

                    ?, ?, ?, ?, ?

                )

                """,

                (

                    student_data[

                        "student_id"

                    ],

                    student_data[

                        "age"

                    ],

                    student_data[

                        "gender"

                    ],

                    student_data[

                        "major"

                    ],

                    student_data[

                        "GPA"

                    ],

                    student_data[

                        "course_load"

                    ],

                    student_data[

                        "avg_course_grade"

                    ],

                    student_data[

                        "attendance_rate"

                    ],

                    enrollment_status,

                    lms_logins,

                    avg_session,

                    assignment_rate,

                    forum_count,

                    video_completion,

                    risk_level

                )

            )


            connection.commit()


        except Exception:

            connection.rollback()


            flash(

                "Unable to add student. The Student ID may already exist.",

                "error"

            )


            connection.close()


            return render_template(

                "add_student_step2.html"

            )


        connection.close()


        # Clear session data

        session.pop(

            "student_data",

            None

        )


        flash(

            "Student added successfully!",

            "success"

        )


        return redirect(

            url_for(

                "students"

            )

        )


    return render_template(

        "add_student_step2.html"

    )


# ============================================================
# EXPORT STUDENTS TO CSV
# ============================================================

@app.route(
    "/export/csv"
)
@login_required
def export_csv():


    connection = get_db_connection()


    students = connection.execute(

        """

        SELECT *

        FROM students

        ORDER BY student_id

        """

    ).fetchall()


    connection.close()


    output = StringIO()


    writer = csv.writer(

        output

    )


    # CSV Header

    writer.writerow([

        "Student ID",

        "Age",

        "Gender",

        "Major",

        "GPA",

        "Course Load",

        "Average Course Grade",

        "Attendance Rate",

        "Enrollment Status",

        "LMS Logins Past Month",

        "Average Session Duration",

        "Assignment Submission Rate",

        "Forum Participation Count",

        "Video Completion Rate",

        "Risk Level"

    ])


    # CSV Data

    for student in students:

        writer.writerow([

            student[

                "student_id"

            ],

            student[

                "age"

            ],

            student[

                "gender"

            ],

            student[

                "major"

            ],

            student[

                "GPA"

            ],

            student[

                "course_load"

            ],

            student[

                "avg_course_grade"

            ],

            student[

                "attendance_rate"

            ],

            student[

                "enrollment_status"

            ],

            student[

                "lms_logins_past_month"

            ],

            student[

                "avg_session_duration_minutes"

            ],

            student[

                "assignment_submission_rate"

            ],

            student[

                "forum_participation_count"

            ],

            student[

                "video_completion_rate"

            ],

            student[

                "risk_level"

            ]

        ])


    response = Response(

        output.getvalue(),

        mimetype=

            "text/csv"

    )


    response.headers[

        "Content-Disposition"

    ] = (

        "attachment; "

        "filename=student_records.csv"

    )


    return response


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(

        debug=True

    )