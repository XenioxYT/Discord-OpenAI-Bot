import json
import sqlite3

db_conn = sqlite3.connect('conversations.db')
db_conn.execute("""
CREATE TABLE IF NOT EXISTS conversations
    (conversation_id INTEGER PRIMARY KEY,
    conversation TEXT,
    is_busy BOOLEAN)
""")

def get_conversation(conversation_id):
    c = db_conn.cursor()
    c.execute("SELECT conversation FROM conversations WHERE conversation_id=?", (conversation_id,))
    result = c.fetchone()
    if result is None:
        return None
    return json.loads(result[0])
