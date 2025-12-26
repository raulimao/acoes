import requests
import sqlite3

BASE_URL = "http://localhost:8000/api"

def verify_api():
    print("🔍 Verifying API Health...")
    try:
        r = requests.get(f"{BASE_URL}/stocks?limit=1")
        if r.status_code == 200:
            print("✅ API /stocks is accessible")
        else:
            print(f"❌ API /stocks failed: {r.status_code}")
            
        # Verify PDF generation
        print("🔍 Verifying PDF Generation...")
        r = requests.get(f"{BASE_URL}/reports/weekly")
        if r.status_code == 200 and r.headers['content-type'] == 'application/pdf':
            print(f"✅ PDF generated successfully ({len(r.content)} bytes)")
        else:
            print(f"❌ PDF generation failed: {r.status_code}")
            
    except Exception as e:
        print(f"❌ API verification failed: {e}")

def verify_db():
    print("\n🔍 Verifying Database Schema...")
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = [c[1] for c in cursor.fetchall()]
        if "is_premium" in columns:
            print("✅ 'is_premium' column exists in users table")
        else:
            print("❌ 'is_premium' column MISSING")
        conn.close()
    except Exception as e:
        print(f"❌ DB verification failed: {e}")

if __name__ == "__main__":
    verify_api()
    verify_db()
