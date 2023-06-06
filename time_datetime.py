from datetime import datetime, timedelta


def time_current_Get():
    """
    Returns the current date and time as a string in the format '%Y-%m-%d %H:%M'.
    """
    return datetime.now().strftime('%Y-%m-%d %H:%M')


def date_current_Get():
    """
    Returns the current date as a string in the format '%Y-%m-%d'.
    """
    return datetime.now().strftime('%Y-%m-%d')


def time_delta():
    """
    Returns a timedelta object representing a time duration of 1 hour.
    """
    return timedelta(hours=1)
