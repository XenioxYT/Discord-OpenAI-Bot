import json
import sqlite3

db_conn = sqlite3.connect('conversations.db')
db_conn.execute("""
CREATE TABLE IF NOT EXISTS conversations
    (conversation_id INTEGER PRIMARY KEY,
    conversation TEXT,
    is_busy BOOLEAN)
""")

def store_conversation(conversation_id, conversation, is_busy=False):
    c = db_conn.cursor()
    values = (conversation_id, json.dumps(conversation), is_busy)
    c.execute("REPLACE INTO conversations VALUES (?, ?, ?)", values)
    db_conn.commit()