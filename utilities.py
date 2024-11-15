import sqlite3
import bcrypt

# Connect to the database
def get_connection():
    conn = sqlite3.connect("beta.db")
    return conn

# Function to authenticate user
def authenticate_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user:
        hashed_password = user[0]
        if bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8")):
            return True
    return False

# Function to add a new user
def add_user(username, password, email):
    conn = get_connection()
    cursor = conn.cursor()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    try:
        cursor.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", 
                       (username, hashed_password, email))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
