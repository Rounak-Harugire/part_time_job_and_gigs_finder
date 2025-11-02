import mysql.connector

def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # Set your MySQL root password if applicable
        database="job_finder"
    )
    return conn
