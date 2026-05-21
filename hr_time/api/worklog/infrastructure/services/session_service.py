from datetime import datetime, date
from typing import Optional, Tuple

from hr_time.api.check_in.repository import CheckinRepository
from hr_time.api.flextime.repository import DurationType


class SessionService:
    """
    Domain service for check-in session calculations.
    Handles extraction of work session start/end times from check-in events.
    """

    @staticmethod
    def get_session_times(
        employee_id: str,
        target_date: Optional[date] = None
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Get session start and end from fresh check-in events.

        Args:
            employee_id: The employee ID
            target_date: Date to fetch check-ins for (defaults to today)

        Returns:
            Tuple of (session_start, session_end) datetimes
        """
        if target_date is None:
            target_date = date.today()

        # Handle if date is a string
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()

        # If date is datetime object, get date part
        if hasattr(target_date, 'date'):
            target_date = target_date.date()

        try:
            checkin_repo = CheckinRepository()
            events_list = checkin_repo.get(target_date, employee_id)

            if not events_list:
                return None, None

            # Get raw events to access timestamps
            events = events_list.events

            # Build map of event ID to timestamp
            event_timestamps = {event.id: event.timestamp for event in events}

            durations = events_list.get_durations()
            if not durations:
                return None, None

            # Find first WORK duration start and last WORK duration end
            session_start = None
            session_end = None

            for duration in durations:
                start_timestamp = event_timestamps.get(duration.event_first)
                end_timestamp = event_timestamps.get(duration.event_second) if duration.event_second else None

                # Only process WORK durations (not BREAK)
                if duration.duration_type != DurationType.BREAK:
                    if session_start is None and start_timestamp:
                        session_start = start_timestamp

                    if end_timestamp:
                        session_end = end_timestamp
                    elif start_timestamp:
                        # No end timestamp (still working), use now
                        session_end = datetime.now()

            # If no end found but we have a start, assume still working
            if session_start and not session_end:
                session_end = datetime.now()

            return session_start, session_end

        except Exception as e:
            import traceback
            traceback.print_exc()
            return None, None
