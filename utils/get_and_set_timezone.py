import sqlite3
import pytz

def get_timezone(discord_id):
    conn = sqlite3.connect('discord_timezones.db')
    c = conn.cursor()
    c.execute("SELECT timezone FROM UserTimezones WHERE discord_id=?", (discord_id,))
    record = c.fetchone()
    conn.close()
    return record[0] if record else 'UTC'

def set_timezone(discord_id, new_timezone):
    conn = sqlite3.connect('discord_timezones.db')
    c = conn.cursor()

    # Check if the timezone is valid
    if new_timezone not in pytz.all_timezones:
        conn.close()
        return False

    # Update or insert the timezone for the user
    c.execute("INSERT OR REPLACE INTO UserTimezones (discord_id, timezone) VALUES (?, ?)", (discord_id, new_timezone))
    
    conn.commit()
    conn.close()
    return True