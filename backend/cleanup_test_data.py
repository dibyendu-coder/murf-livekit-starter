import sys
sys.path.insert(0, 'src')
import sqlite3
from database import _DB_PATH

conn = sqlite3.connect(_DB_PATH)
conn.execute("DELETE FROM escalations WHERE learner_id='test_user'")
conn.commit()
conn.close()
print("Test data cleaned up.")
