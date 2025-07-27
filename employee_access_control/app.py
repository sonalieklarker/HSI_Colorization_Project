from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import errorcode, IntegrityError
import hashlib
from functools import wraps

app = Flask(__name__)
app.secret_key = "your_secret_key"  # ❗ Change this before production

# ─────────────────────────  DB CONNECTION  ──────────────────────────
db = mysql.connector.connect(
    host="localhost",
    user="root",                    # ← your MySQL user
    password="momdad#2817",         # ← your MySQL password
    database="EMP",
    auth_plugin="mysql_native_password"  # needed on some MySQL installs
)
# Every query will return dictionaries instead of tuples
db_cursor = db.cursor(dictionary=True)
# ────────────────────────────────────────────────────────────────────


# ──────────────  UTILITY & DECORATORS  ──────────────
def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if session.get("role") not in allowed_roles:
                flash("You don’t have permission to access this page.", "danger")
                return redirect(url_for("unauthorized"))
            return f(*args, **kwargs)
        return wrapper
    return decorator
# ─────────────────────────────────────────────────────


@app.route("/")
def home():
    return redirect(url_for("login"))


# ───────────────  LOGIN / LOGOUT  ───────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = hash_password(request.form["password"])

        query = """
        SELECT e.id, e.username, r.role_name
        FROM employees AS e
        JOIN roles AS r ON e.role_id = r.id
        WHERE e.username = %s AND e.password = %s
        """
        db_cursor.execute(query, (username, password))
        user = db_cursor.fetchone()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role_name"]
            flash(f"Welcome {user['username']}!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have logged out.", "info")
    return redirect(url_for("login"))
# ────────────────────────────────────────────────


# ───────────────  DASHBOARD  ───────────────
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template(
        "dashboard.html",
        username=session["username"],
        role=session["role"]
    )
# ───────────────────────────────────────────


# ───────────────  PROFILE  ───────────────
@app.route("/profile")
@login_required
def profile():
    user_id = session["user_id"]

    query = """
    SELECT e.id, e.username, r.role_name
    FROM employees e
    JOIN roles r ON e.role_id = r.id
    WHERE e.id = %s
    """
    db_cursor.execute(query, (user_id,))
    user = db_cursor.fetchone()

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("dashboard"))

    return render_template("profile.html", user=user)
# ───────────────────────────────────────────


# ───────────────  EMPLOYEE CRUD  ───────────────
@app.route("/employees")
@login_required
@role_required(["Admin", "Manager"])
def employee_list():
    search = request.args.get("search", "")
    if search:
        sql = """
        SELECT e.id, e.username, r.role_name
        FROM employees AS e JOIN roles AS r ON e.role_id = r.id
        WHERE e.username LIKE %s ORDER BY e.username
        """
        db_cursor.execute(sql, (f"%{search}%",))
    else:
        sql = """
        SELECT e.id, e.username, r.role_name
        FROM employees AS e JOIN roles AS r ON e.role_id = r.id
        ORDER BY e.username
        """
        db_cursor.execute(sql)
    employees = db_cursor.fetchall()
    return render_template(
        "employee_list.html",
        employees=employees,
        role=session["role"],
        search=search
    )

@app.route("/employee/add", methods=["GET", "POST"])
@login_required
@role_required(["Admin"])
def employee_add():
    if request.method == "POST":
        username   = request.form["username"]
        password   = hash_password(request.form["password"])
        role_id    = request.form["role_id"]

        try:
            db_cursor.execute(
                "INSERT INTO employees (username, password, role_id) VALUES (%s, %s, %s)",
                (username, password, role_id)
            )
            db.commit()
            flash(f"Employee '{username}' added successfully.", "success")
            return redirect(url_for("employee_list"))
        except IntegrityError as err:
            if err.errno == errorcode.ER_DUP_ENTRY:
                flash("Username already exists. Choose a different one.", "danger")
            else:
                flash("Database error.", "danger")

    db_cursor.execute("SELECT * FROM roles")
    roles = db_cursor.fetchall()
    return render_template("employee_form.html", action="Add", roles=roles)

@app.route("/employee/edit/<int:employee_id>", methods=["GET", "POST"])
@login_required
@role_required(["Admin", "Manager"])
def employee_edit(employee_id):
    db_cursor.execute("SELECT * FROM employees WHERE id = %s", (employee_id,))
    employee = db_cursor.fetchone()
    if not employee:
        flash("Employee not found.", "danger")
        return redirect(url_for("employee_list"))

    db_cursor.execute("SELECT * FROM roles")
    roles = db_cursor.fetchall()

    # Managers can only edit Employees
    if session["role"] == "Manager":
        db_cursor.execute("SELECT role_name FROM roles WHERE id = %s", (employee["role_id"],))
        emp_role = db_cursor.fetchone()
        if emp_role["role_name"] != "Employee":
            flash("Managers can only edit Employees.", "danger")
            return redirect(url_for("employee_list"))

    if request.method == "POST":
        username = request.form["username"]
        role_id  = request.form["role_id"]

        try:
            if request.form["password"]:
                password = hash_password(request.form["password"])
                sql = """
                UPDATE employees SET username=%s, password=%s, role_id=%s WHERE id=%s
                """
                db_cursor.execute(sql, (username, password, role_id, employee_id))
            else:
                sql = "UPDATE employees SET username=%s, role_id=%s WHERE id=%s"
                db_cursor.execute(sql, (username, role_id, employee_id))
            db.commit()
            flash("Employee updated successfully.", "success")
            return redirect(url_for("employee_list"))
        except IntegrityError as err:
            if err.errno == errorcode.ER_DUP_ENTRY:
                flash("Username already exists. Choose a different one.", "danger")
            else:
                flash("Database error.", "danger")

    return render_template(
        "employee_form.html",
        action="Edit",
        employee=employee,
        roles=roles
    )

@app.route("/employee/delete/<int:employee_id>", methods=["POST"])
@login_required
@role_required(["Admin"])
def employee_delete(employee_id):
    db_cursor.execute("DELETE FROM employees WHERE id=%s", (employee_id,))
    db.commit()
    flash("Employee deleted successfully.", "success")
    return redirect(url_for("employee_list"))
# ───────────────────────────────────────────────


@app.route("/unauthorized")
def unauthorized():
    return render_template("unauthorized.html"), 403


# ─────────────── PASSWORD HASH UPDATE SCRIPT (RUN ONCE) ───────────────
@app.route("/update_passwords")
@login_required
@role_required(["Admin"])
def update_passwords():
    """
    Run this once to hash any plain-text passwords currently in DB.
    Remove or disable this route after running.
    """
    db_cursor.execute("SELECT id, password FROM employees")
    users = db_cursor.fetchall()
    updated_count = 0

    for user in users:
        pw = user["password"]
        # Check if already hashed: SHA256 hex length = 64 chars, hex digits only
        if len(pw) != 64 or not all(c in "0123456789abcdef" for c in pw.lower()):
            hashed_pw = hash_password(pw)
            db_cursor.execute("UPDATE employees SET password=%s WHERE id=%s", (hashed_pw, user["id"]))
            updated_count += 1

    db.commit()
    flash(f"Updated {updated_count} passwords to hashed versions.", "success")
    return redirect(url_for("employee_list"))


# ───────────────  RUN  ───────────────
if __name__ == "__main__":
    app.run(debug=True)
