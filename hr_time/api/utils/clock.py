import datetime


class Clock:
    def date_today(self) -> datetime.date:
        return datetime.date.today()

    def now(self) -> datetime.datetime:
        return datetime.datetime.now()
    
    @staticmethod
    def format_time_am_pm(dt: datetime.datetime) -> str:
        """
        Extracts the time in AM/PM format from a given datetime object.

        Args:
            dt (datetime.datetime): The datetime object to extract the time from.

        Returns:
            str: Time in 'HH:MM AM/PM' format.
        """
        return dt.strftime('%I:%M %p')