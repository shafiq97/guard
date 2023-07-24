from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import pymysql
from datetime import datetime
import os
import json


app = Flask(__name__)
app.secret_key = "1234"  # replace 'your secret key' with your actual secret key

@app.route("/payroll")
def payroll():
    user_id = session["user_id"]

    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="recruit",
        cursorclass=pymysql.cursors.DictCursor,

    )

    try:
        with conn.cursor() as cursor:
            # Get the current month and year
            current_month = datetime.now().month
            current_year = datetime.now().year

            # SQL query to get attendance for the current month
            sql = """
            SELECT * FROM attendance 
            INNER JOIN users ON attendance.user_id = users.id 
            WHERE users.id = %s AND MONTH(attendance.date) = %s AND YEAR(attendance.date) = %s
            """
            cursor.execute(sql, (user_id, current_month, current_year))
            attendance = cursor.fetchall()

            # Calculate the total salary
            working_days = len(attendance)
            salary = attendance[0]['salary'] if attendance else 0
            total_salary = salary * working_days

    finally:
        conn.close()

    return render_template("payroll.html", attendance=attendance, total_salary=total_salary)

@app.route("/post_record", methods=["GET"])
def post_record():
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="recruit",
        cursorclass=pymysql.cursors.DictCursor,
    )

    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM posts inner join users on posts.recruiter_id = users.id WHERE recruiter_id = %s"
            cursor.execute(sql, (session["user_id"],))
            posts = cursor.fetchall()
    finally:
        conn.close()

    return render_template("post_record.html", posts=posts)


@app.route("/user_profile")
def user_profile():
    # Connect to the database
    user_id = session.get('user_id')
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="recruit",
        cursorclass=pymysql.cursors.DictCursor,
    )

    try:
        with conn.cursor() as cursor:
            # Fetch the user data from the database
            sql = "SELECT * FROM users WHERE id = %s"
            cursor.execute(sql, (user_id,))
            user = cursor.fetchone()
    finally:
        conn.close()

    # Pass the user data to the template
    return render_template("user_profile.html", user=user)


@app.route("/staff_login", methods=["POST", "GET"])
def staff_login():
    if request.method == "POST":
        # Extract the username and password from the form data
        username = request.form.get("username")
        password = request.form.get("password")

        # Connect to your database and retrieve user information
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="",
            database="recruit",
            cursorclass=pymysql.cursors.DictCursor,
        )

        try:
            with conn.cursor() as cursor:
                # Find the user based on the username
                sql = "SELECT * FROM users WHERE username = %s"
                cursor.execute(sql, (username,))
                result = cursor.fetchone()
        finally:
            conn.close()

        # Check if the user exists and the password is correct
        if result is not None and result["password"] == password:
            # Login successful
            # Here you may want to start a session or redirect the user to a different page
            session["user_id"] = result["id"]
            return redirect(url_for("user_profile", user_id=result["id"]))

        else:
            # Login failed
            # Render the login template again with an error message
            return render_template(
                "staff_login.html", error="Incorrect username or password."
            )

    # GET request
    return render_template("staff_login.html")


@app.route("/delete_attendance", methods=["POST"])
def delete_attendance():
    # Extract attendance_id from form data
    attendance_id = request.form.get("attendance_id")

    # Delete the attendance record from the database based on the attendance ID
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="recruit",
        cursorclass=pymysql.cursors.DictCursor,
    )

    try:
        with conn.cursor() as cursor:
            # Assuming you have an 'attendance' table in the database
            sql = "DELETE FROM attendance WHERE id = %s"
            cursor.execute(sql, (attendance_id,))
        conn.commit()
    finally:
        conn.close()

    # Return a response indicating the deletion was successful
    return redirect(
        url_for("mark_attendance")
    )  # Replace with your actual attendance page route


@app.route("/edit_attendance", methods=["POST"])
def edit_attendance():
    # Get data from the form
    attendance_id = request.form.get("attendance_id")
    duty_date = request.form.get("duty_date")
    time_in = request.form.get("time_in")
    time_out = request.form.get("time_out")
    status = request.form.get("status")

    print("Attendance ID:", attendance_id)
    print("Duty Date:", duty_date)
    print("Time In:", time_in)
    print("Time Out:", time_out)
    print("Status:", status)

    # Connect to the database
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="recruit",
        cursorclass=pymysql.cursors.DictCursor,
    )

    try:
        with conn.cursor() as cursor:
            # Update attendance record
            sql = """
                UPDATE attendance
                SET time_in = %s, time_out = %s, status = %s, date = %s
                WHERE id = %s
            """
            cursor.execute(sql, (time_in, time_out, status, duty_date, attendance_id))
            conn.commit()

    finally:
        conn.close()

    return redirect(url_for("mark_attendance"))


@app.route("/submit_attendance", methods=["POST"])
def submit_attendance():
    # Retrieve form data
    recruiter_id = request.form.get("recruiter_id")
    time_in = request.form.get("time_in")
    time_out = request.form.get("time_out")
    duty_date = request.form.get("duty_date")
    status = request.form.get("status")

    if not status:
        status = "absent"

    # Convert the duty_date string to a date object
    duty_date = datetime.strptime(duty_date, "%Y-%m-%d").date()

    # Save data to MySQL database
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="recruit",
        cursorclass=pymysql.cursors.DictCursor,
    )

    try:
        with conn.cursor() as cursor:
            # Assuming you have a 'attendance' table in the database with appropriate columns
            sql = """
                INSERT INTO attendance (user_id, time_in, time_out, date, status)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(
                sql,
                (
                    recruiter_id,
                    time_in,
                    time_out,
                    duty_date,
                    status,
                ),
            )
        conn.commit()
    finally:
        conn.close()

    # Redirect to the main page after form submission
    return redirect(url_for("mark_attendance"))


@app.route("/mark_attendance", methods=["POST", "GET"])
def mark_attendance():
    # Fetch recruiter, post and attendance data from the database
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="recruit",
        cursorclass=pymysql.cursors.DictCursor,
    )

    recruiters = []
    posts = []
    attendances = []
    try:
        with conn.cursor() as cursor:
            # Fetch recruiters data
            sql = "SELECT * FROM users WHERE role = 'recruiter'"
            cursor.execute(sql)
            recruiters = cursor.fetchall()

            # Fetch posts data
            sql = "SELECT * FROM posts"
            cursor.execute(sql)
            posts = cursor.fetchall()

            # Fetch attendance data
            sql = "SELECT * FROM attendance inner join users on attendance.user_id = users.id"
            cursor.execute(sql)
            attendances = cursor.fetchall()

    finally:
        conn.close()

    return render_template(
        "attendance.html", recruiters=recruiters, posts=posts, attendances=attendances
    )


@app.route("/delete_post/<int:post_id>", methods=["POST"])
def delete_post(post_id):
    # Delete the post from the database based on the post ID
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="recruit",
        cursorclass=pymysql.cursors.DictCursor,
    )

    try:
        with conn.cursor() as cursor:
            # Assuming you have a 'posts' table in the database
            sql = "DELETE FROM posts WHERE id = %s"
            cursor.execute(sql, post_id)
        conn.commit()
    finally:
        conn.close()

    # Return a response indicating the deletion was successful
    return redirect(url_for("assign_post"))


@app.route("/edit_posts/<int:post_id>", methods=["GET", "POST"])
def edit_posts(post_id):
    if request.method == "POST":
        # Retrieve form data
        recruiter_id = request.form.get("recruiter_id")
        post_location = request.form.get("post_location")
        duty_time = request.form.get("duty_time")
        duty_date = request.form.get("duty_date")
        status = request.form.get("status")

        # Convert the duty_date string to a date object
        duty_date = datetime.datetime.strptime(duty_date, "%Y-%m-%d").date()

        # Save data to MySQL database
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="",
            database="recruit",
            cursorclass=pymysql.cursors.DictCursor,
        )

        try:
            with conn.cursor() as cursor:
                # Assuming you have a 'posts' table in the database with appropriate columns
                sql = """
                    UPDATE posts SET
                    recruiter_id = %s,
                    post_location = %s,
                    duty_time = %s,
                    duty_date = %s,
                    status = %s
                    WHERE id = %s
                """
                cursor.execute(
                    sql,
                    (
                        recruiter_id,
                        post_location,
                        duty_time,
                        duty_date,
                        status,
                        post_id,
                    ),
                )
            conn.commit()
        finally:
            conn.close()

        return redirect(url_for("assign_post"))

    # Fetch post data from the database based on the post ID
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="recruit",
        cursorclass=pymysql.cursors.DictCursor,
    )

    try:
        with conn.cursor() as cursor:
            # Assuming you have a 'posts' table in the database
            sql = "SELECT * FROM posts WHERE id = %s"
            cursor.execute(sql, post_id)
            post = cursor.fetchone()
    finally:
        conn.close()

    return render_template("edit_post.html", post=post)


@app.route("/assign_post", methods=["GET"])
def assign_post():
    # Fetch recruiter and post data from the database
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="recruit",
        cursorclass=pymysql.cursors.DictCursor,
    )

    recruiters = []
    posts = []
    try:
        with conn.cursor() as cursor:
            # Assuming you have a 'users' table in the database
            sql = "SELECT id, name FROM users WHERE role = 'recruiter'"
            cursor.execute(sql)
            recruiters = cursor.fetchall()

            # Fetch posts data
            sql = "SELECT * FROM posts"
            cursor.execute(sql)
            posts = cursor.fetchall()
    finally:
        conn.close()

    return render_template("assign_post.html", recruiters=recruiters, posts=posts)


@app.route("/submit_post", methods=["POST"])
def submit_post():
    # Retrieve form data
    recruiter_id = request.form.get("recruiter_id")
    post_location = request.form.get("post_location")
    duty_time = request.form.get("duty_time")
    duty_date = request.form.get("duty_date")
    status = request.form.get("status")

    # Convert the duty_date string to a date object
    duty_date = datetime.datetime.strptime(duty_date, "%Y-%m-%d").date()

    # Save data to MySQL database
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="recruit",
        cursorclass=pymysql.cursors.DictCursor,
    )

    try:
        with conn.cursor() as cursor:
            # Assuming you have a 'posts' table in the database with appropriate columns
            sql = """
                INSERT INTO posts (recruiter_id, post_location, duty_time, duty_date, status)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(
                sql,
                (
                    recruiter_id,
                    post_location,
                    duty_time,
                    duty_date,
                    status
                ),
            )
        conn.commit()
    finally:
        conn.close()

    # Redirect to the main page after form submission
    return redirect(url_for("assign_post"))


@app.route("/delete_user", methods=["POST"])
def delete_user():
    user_id = request.form.get("user_id")

    # Delete the user from the database based on the user ID
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="recruit",
        cursorclass=pymysql.cursors.DictCursor,
    )

    try:
        with conn.cursor() as cursor:
            # Assuming you have a 'users' table in the database
            sql = "DELETE FROM users WHERE id = %s"
            cursor.execute(sql, user_id)
        conn.commit()
    finally:
        conn.close()

    # Return a response indicating the deletion was successful
    return "User deleted successfully"


@app.route("/edit/<int:user_id>", methods=["GET", "POST"])
def edit_user(user_id):
    if request.method == "POST":
        # Retrieve form data and update the user in the database
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="",
            database="recruit",
            cursorclass=pymysql.cursors.DictCursor,
        )

        try:
            with conn.cursor() as cursor:
                # Assuming you have a 'users' table in the database with appropriate columns
                sql = """
                    UPDATE users SET
                    name = %s,
                    phone = %s,
                    email = %s,
                    address = %s,
                    gender = %s,
                    origin = %s,
                    relationship = %s,
                    religion = %s,
                    dob = %s,
                    username = %s,
                    password = %s
                    WHERE id = %s
                """
                cursor.execute(
                    sql,
                    (
                        request.form.get("name"),
                        request.form.get("phone"),
                        request.form.get("email"),
                        request.form.get("address"),
                        request.form.get("gender"),
                        request.form.get("origin"),
                        request.form.get("relationship"),
                        request.form.get("religion"),
                        request.form.get("dob"),
                        request.form.get("username"),
                        request.form.get("password"),
                        user_id,
                    ),
                )
            conn.commit()
        finally:
            conn.close()

        return redirect(url_for("main_page"))

    # Fetch user data from the database based on the user ID
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="recruit",
        cursorclass=pymysql.cursors.DictCursor,
    )

    try:
        with conn.cursor() as cursor:
            # Assuming you have a 'users' table in the database
            sql = "SELECT * FROM users WHERE id = %s"
            cursor.execute(sql, user_id)
            user = cursor.fetchone()
    finally:
        conn.close()

    return render_template("edit.html", user=user)


@app.route("/get_user", methods=["POST"])
def get_user():
    user_id = request.form.get("user_id")

    # Fetch user data from the database based on the user ID
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="recruit",
        cursorclass=pymysql.cursors.DictCursor,
    )

    try:
        with conn.cursor() as cursor:
            # Assuming you have a 'users' table in the database
            sql = "SELECT * FROM users WHERE id = %s"
            cursor.execute(sql, user_id)
            user = cursor.fetchone()
    finally:
        conn.close()
    print(str(user))
    return jsonify(user)


@app.route("/main_page")
def main_page():
    # Fetch user data from the database (example)
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="recruit",
        cursorclass=pymysql.cursors.DictCursor,
    )

    try:
        with conn.cursor() as cursor:
            # Assuming you have a 'users' table in the database
            sql = "SELECT * FROM users"
            cursor.execute(sql)
            users = cursor.fetchall()
    finally:
        conn.close()

    date = datetime.now().strftime("%B %d, %Y")
    time = datetime.now().strftime("%I:%M:%S %p")
    return render_template("main.html", date=date, time=time, users=users)


@app.route("/submit", methods=["POST"])
def submit():
    # Retrieve form data
    id = request.form.get("id")
    name = request.form.get("name")
    phone = request.form.get("phone")
    email = request.form.get("email")
    address = request.form.get("address")
    gender = request.form.get("gender")
    origin = request.form.get("origin")
    relationship = request.form.get("relationship")
    religion = request.form.get("religion")
    dob = request.form.get("dob")
    username = request.form.get("username")
    password = request.form.get("password")
    salary = request.form.get("salary")

    dob = datetime.datetime.strptime(dob, "%Y-%m-%d").date() if dob else None

    # Handle avatar file upload
    avatar = request.files.get("avatar")
    avatar_filename = None
    # print(str(secure_filename(avatar.filename)))
    if avatar:
        avatar_filename = secure_filename(avatar.filename)
        avatar.save(os.path.join(app.config["UPLOAD_FOLDER"], avatar_filename))

    # Save data to MySQL database
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="recruit",
        cursorclass=pymysql.cursors.DictCursor,
    )

    try:
        with conn.cursor() as cursor:
            # Assuming you have a 'users' table in the database with appropriate columns
            sql = sql = """
                INSERT INTO users (id, name, phone, email, address, gender, origin, relationship, religion, dob, username, password, avatar, salary)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                sql,
                (
                    id,
                    name,
                    phone,
                    email,
                    address,
                    gender,
                    origin,
                    relationship,
                    religion,
                    dob,
                    username,
                    password,
                    avatar_filename,
                    salary
                ),
            )
        conn.commit()
    finally:
        conn.close()

    # Redirect to the main page after form submission
    return redirect(url_for("main_page"))


@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get(
            "username"
        )  # Retrieve the username from the form data
        password = request.form.get(
            "password"
        )  # Retrieve the password from the form data

        # Check if the provided username and password are correct
        if username == "admin" and password == "admin":
            return redirect(url_for("main_page"))  # Redirect to the main page route

        # If the username and password are incorrect, you can display an error message or perform any other actions

    # Render the login form template for GET requests or if the login was unsuccessful
    return render_template("admin_login.html")


@app.route("/")
def home():
    date = datetime.now().strftime("%B %d, %Y")
    time = datetime.now().strftime("%I:%M:%S %p")
    return render_template("index.html", date=date, time=time)


if __name__ == "__main__":
    app.config["UPLOAD_FOLDER"] = "static/avatar"
    app.run(debug=True, port=5001)
