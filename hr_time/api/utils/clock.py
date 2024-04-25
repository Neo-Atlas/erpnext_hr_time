import datetime


class Clock:
    def date_today(self) -> datetime.date:
        return datetime.date.today()

    def now(self) -> datetime.datetime:
        return datetime.datetime.now()
