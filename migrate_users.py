import sqlite3
from pathlib import Path

DATABASE_PATH = Path("users.db")

def migrate():
    print(f"Migrating database at {DATABASE_PATH.absolute()}...")
    conn = sqlite3.connect(str(DATABASE_PATH))
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "is_premium" not in columns:
            print("Adding is_premium column...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_premium BOOLEAN DEFAULT 0")
            conn.commit()
            print("✅ Migration successful: is_premium column added.")
        else:
            print("ℹ️ Column is_premium already exists.")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
