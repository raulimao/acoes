import sqlite3

import bcrypt

def connect_db():
    conn = sqlite3.connect('users.db')
    return conn

def create_users_table():
    conn = connect_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def close_db(conn):
    """Close the database connection"""
    if conn:
        conn.close()

def add_user(username, name, email, password):
    """Add a new user to the users table with a hashed password."""
    conn = connect_db()
    c = conn.cursor()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        c.execute('INSERT INTO users (username, name, email, password) VALUES (?, ?, ?, ?)', (username, name, email, hashed_password))
        conn.commit()
 return True # User added successfully
    except sqlite3.IntegrityError:
 return False # Username already exists
    finally:
        close_db(conn)

def get_user(username):
    """Retrieve user data by username."""
    conn = connect_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    close_db(conn)
 return user # Returns a tuple (username, name, email, password) or None

if __name__ == '__main__':
    create_users_table()
    print("Database and users table created successfully.")
import sqlite3

DATABASE_NAME = 'users.db'
import bcrypt

def connect_db():
    conn = sqlite3.connect('users.db')
    return conn

def create_users_table():
    conn = connect_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def close_db(conn):
    """Close the database connection"""
    if conn:
        conn.close()

def add_user(username, name, email, password):
    conn = connect_db()
    c = conn.cursor()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        c.execute('INSERT INTO users (username, name, email, password) VALUES (?, ?, ?, ?)', (username, name, email, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Username already exists
    finally:
        close_db(conn)

def get_user(username):
    conn = connect_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    close_db(conn)
    return user

if __name__ == '__main__':
    create_users_table()
    print("Database and users table created successfully.")