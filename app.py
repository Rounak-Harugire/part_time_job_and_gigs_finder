from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from config import get_db_connection
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__, template_folder='templates')
app.secret_key = "supersecretkey"

# 🔹 Home Page
@app.route('/')
def home():
    return render_template('index.html')

# 🔹 Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        user_type = request.form['user_type']  # employee or employer

        if not name or not email or not password:
            flash("All fields are required!", "danger")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)  # Secure password

        conn = get_db_connection()  # Get DB connection
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO users (name, email, phone, password, user_type) VALUES (%s, %s, %s, %s, %s)", 
                           (name, email, phone, hashed_password, user_type))
            conn.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Error: {e}", "danger")
            conn.rollback()  # Use `conn.rollback()` instead of `db.rollback()`
        finally:
            cursor.close()
            conn.close()  # Close the connection

    return render_template('register.html')


# 🔹 Job Posting Route (Only for Employers)
@app.route('/post_job', methods=['GET', 'POST'])
def post_job():
    if 'user_id' not in session or session['user_type'] != 'employer':
        return "You must be logged in as an employer to post a job.", 403

    if request.method == 'POST':
        title = request.form['title']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        duration = request.form['duration']
        employer_id = session['user_id']

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO jobs (title, email, phone, address, duration, employer_id) VALUES (%s, %s, %s, %s, %s, %s)",
                (title, email, phone, address, duration, employer_id)
            )
            conn.commit()
            return redirect(url_for('jobs'))
        except mysql.connector.Error as e:
            flash(f"Error: {e}", "danger")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()  # Ensure the connection is always closed

    return render_template('post_job.html')

# 🔹 Job Listings (For Employees)
@app.route('/jobs')
def jobs():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    sql = """SELECT jobs.*, users.name AS employer_name
             FROM jobs
             JOIN users ON jobs.employer_id = users.id"""
    
    cursor.execute(sql)
    jobs = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('jobs.html', jobs=jobs)

@app.route('/update_job/<int:job_id>', methods=['GET', 'POST'])
def update_job(job_id):
    if 'user_id' not in session or session['user_type'] != 'employer':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 🔹 Check if the employer owns this job
    cursor.execute("SELECT * FROM jobs WHERE id=%s AND employer_id=%s", (job_id, session['user_id']))
    job = cursor.fetchone()

    if not job:
        return "Job not found or unauthorized!", 403

    if request.method == 'POST':
        title = request.form['title']
        address = request.form['address']
        duration = request.form['duration']

        cursor.execute("UPDATE jobs SET title=%s, address=%s, duration=%s WHERE id=%s AND employer_id=%s",
                       (title, address, duration, job_id, session['user_id']))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('jobs'))

    cursor.close()
    conn.close()
    return render_template('update_job.html', job=job)

@app.route('/delete_job/<int:job_id>')
def delete_job(job_id):
    if 'user_id' not in session or session['user_type'] != 'employer':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM jobs WHERE id=%s AND employer_id=%s", (job_id, session['user_id']))
    conn.commit()

    cursor.close()
    conn.close()
    return redirect(url_for('jobs'))


# 🔹 Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_type'] = user['user_type']

            # 🔹 Redirect based on user type
            if user['user_type'] == 'employer':
                return redirect(url_for('post_job'))
            return redirect(url_for('jobs'))

        return "Invalid credentials!"

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_type', None)
    return redirect(url_for('login'))


@app.route('/apply/<int:job_id>')
def apply(job_id):
    if 'user_id' not in session or session['user_type'] != 'employee':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if the user has already applied
    cursor.execute("SELECT * FROM job_applications WHERE job_id=%s AND employee_id=%s", 
                   (job_id, session['user_id']))
    existing_application = cursor.fetchone()

    if existing_application:
        return "You have already applied for this job."

    # Insert application into database
    cursor.execute("INSERT INTO job_applications (job_id, employee_id) VALUES (%s, %s)", 
                   (job_id, session['user_id']))
    conn.commit()

    cursor.close()
    conn.close()
    
    return "Application submitted successfully!"

@app.route('/my_applications')
def my_applications():
    if 'user_id' not in session or session['user_type'] != 'employee':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    sql = """
        SELECT jobs.title, jobs.address, jobs.duration, users.name AS employer_name, 
               job_applications.application_date 
        FROM job_applications 
        JOIN jobs ON job_applications.job_id = jobs.id
        JOIN users ON jobs.employer_id = users.id
        WHERE job_applications.employee_id = %s
    """
    
    cursor.execute(sql, (session['user_id'],))
    applications = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('my_applications.html', applications=applications)

@app.route('/view_applications')
def view_applications():
    if 'user_id' not in session or session['user_type'] != 'employer':
        return redirect(url_for('login'))

    employer_id = session['user_id']
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch applications for jobs posted by this employer
    sql = """SELECT job_applications.id AS application_id, job_applications.applied_at, 
                    users.name AS employee_name, users.email AS employee_email, 
                    jobs.title AS job_title, jobs.id AS job_id
             FROM job_applications
             JOIN jobs ON job_applications.job_id = jobs.id
             JOIN users ON job_applications.employee_id = users.id
             WHERE jobs.employer_id = %s"""
    
    cursor.execute(sql, (employer_id,))
    applications = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('view_applications.html', applications=applications)

if __name__ == '__main__':
    app.run(debug=True)
