import datetime
from typing import Optional

from hr_time.api import logger
from hr_time.api.check_in.event import CheckinEvent
from hr_time.api.flextime.repository import CheckinDuration
from hr_time.api.shared.utils.clock import Clock


class CheckinList:
    events: list[CheckinEvent]

    def __init__(self, events: list[CheckinEvent]):
        self.events = events

    # Processes the event list and builds durations
    def get_durations(self) -> list[CheckinDuration]:
        if not self.events:
            return []

        durations = []
        current = None

        for event in self.events:
            if current is None:
                current = event
                continue

            # Cannot start with a non-break OUT event
            if (not current.is_in) and (not current.is_break):
                logger.info("Unable to match checkin event " + current.id)
                current = event
                continue

            # Matching OUT event to current IN event
            if current.is_in and (not current.is_break):
                if not event.is_in:
                    durations.append(CheckinDuration.build_from_events(current, event))

                    if event.is_break:
                        current = event
                    else:
                        current = None

                    continue
                else:
                    logger.info("Skipping double checkin event " + event.id)
                    continue

            # Currently in break, searching for IN event
            if (not current.is_in) and current.is_break:
                if event.is_in:
                    durations.append(CheckinDuration.build_from_events(current, event))
                    current = event

        return durations

    def get_latest(self) -> Optional[CheckinEvent]:
        if not self.events:
            return None

        return self.events[-1]

    # Returns true if at leas one break event exists
    def has_break(self) -> bool:
        for event in self.events:
            if event.is_break:
                return True

        return False

    # Adds a closing checkin event for the current duration
    def close_current(self, clock: Clock = Clock()):
        latest = self.get_latest()

        if latest is None:
            return

        if (not latest.is_in) and (not latest.is_break):
            return

        if latest.is_in:
            self.events.append(CheckinEvent("Simulated", clock.now(), False, False))
            return

        self.events.append(CheckinEvent("Simulated", clock.now(), True, False))
