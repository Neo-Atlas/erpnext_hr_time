import datetime


class CheckinEvent:
    # Document ID
    id: str

    # Timestamp of stamp event
    timestamp: datetime.datetime

    # True if Checkin, False if Checkout
    is_in: bool

    # True if checked out for break
    is_break: bool

    def __init__(self, name: str, timestamp: datetime, is_in: bool, is_break: bool):
        self.id = name
        self.is_break = is_break
        self.is_in = is_in
        self.timestamp = timestamp
