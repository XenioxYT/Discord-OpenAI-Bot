import datetime
import pytz

def get_date_time(timezone="UTC"):
    now = datetime.datetime.now(pytz.timezone(timezone))
    return now.strftime("%Y-%m-%d %H:%M:%S")
