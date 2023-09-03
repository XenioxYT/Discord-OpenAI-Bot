import shutil
import os
import sqlite3

def check_user_level(user_id):
    # Create a temporary copy of the database
    temp_db_path = "temp_users.db"
    shutil.copy('/home/gpu/xp-bot/users.db', temp_db_path)

    # Connect to the temporary database and fetch data
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()

    cursor.execute('SELECT level FROM users WHERE user_id=?', (user_id,))
    result = cursor.fetchone()

    conn.close()

    # Delete the temporary database
    os.remove(temp_db_path)

    if result:
        return result[0]
    else:
        return 0
