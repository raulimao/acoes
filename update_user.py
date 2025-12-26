import sqlite3
import os

# Database is in the same directory as this script
db_path = 'users.db'

print(f"Connecting to {db_path}...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

email = 'teste@teste.com'

# Check if user exists
cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
user = cursor.fetchone()

if user:
    print(f"User found: {user[2]} (Current premium: {user[4]})")
    
    # Update to premium
    cursor.execute("UPDATE users SET is_premium = 1 WHERE email = ?", (email,))
    conn.commit()
    
    print(f"User {email} updated to Premium status.")
    
    # Verify
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    print(f"Verification: {user[2]} (New premium: {user[4]})")
    
else:
    print(f"User {email} not found in database.")

conn.close()
