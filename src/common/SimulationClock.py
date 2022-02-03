from datetime import datetime, timedelta

START_DATETIME = datetime(2020, 1, 1, 0, 0, 0, 0)
DATETIME = datetime(2020, 1, 1, 0, 0, 0, 0)

def updateSimulationClock(secondsPerTick):
    global DATETIME
    DATETIME_before = DATETIME
    DATETIME = DATETIME + timedelta(seconds=secondsPerTick)
    return not (DATETIME.day == DATETIME_before.day)

def getDateTime():
    global DATETIME
    return DATETIME

def getMillisecondsSinceStart():
    global DATETIME
    global START_DATETIME
    duration = DATETIME - START_DATETIME
    return int(duration.total_seconds() * 1000)


def timestampToMillisecondsSinceStart(timestamp):
    global START_DATETIME
    duration = timestamp - START_DATETIME
    return int(duration.total_seconds() * 1000)


def toDateTime(milliseconds):
    global START_DATETIME
    return START_DATETIME + timedelta(milliseconds=milliseconds)

