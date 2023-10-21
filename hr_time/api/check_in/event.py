import datetime


class CheckinEvent:
    # Document ID
    id: str

    # Timestamp of stamp event
    timestamp: datetime.datetime

    # True if Checkin, False if Checkout
    is_in: bool

    # True if checked out for brake
    is_brake: bool

    def __init__(self, name: str, timestamp: datetime, is_in: bool, is_brake: bool):
        self.id = name
        self.is_brake = is_brake
        self.is_in = is_in
        self.timestamp = timestamp
