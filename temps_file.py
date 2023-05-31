import ujson as json
import utime
import uos

TEMPS_FILE = "temps.json"
MAX_FILE_AGE = 600  # Maximum age of the file in seconds (10 mins) allowed


def load_temps():
    """Return the last recorded max / min temperature and count of temperature
    readings provided those readings haven't exceeded the maximum age
    allowed. This is useful if the machine has restarted and allows max/min
    temperature recording to continue."""
    try:
        file_stats = uos.stat(TEMPS_FILE)
        # Index 8 represents the file's modified time
        modified_time = file_stats[8]
        time_now = utime.time()
        if time_now - modified_time < MAX_FILE_AGE:
            with open(TEMPS_FILE, "r") as datafile:
                temp_data = json.load(datafile)
                return temp_data.get("max_temp"), temp_data.get("min_temp"), \
                    temp_data.get("count")
    except OSError:
        # File doesn't exist or couldn't be read
        pass

    return None, None, 0


def save_temps(max_temp, min_temp, count):
    """Save the current max/min temps and readings count to file in
    JSON format"""
    # Save the variables' values
    data = {"max_temp": max_temp, "min_temp": min_temp,
            "count": count}
    with open(TEMPS_FILE, "w") as datafile:
        json.dump(data, datafile)
