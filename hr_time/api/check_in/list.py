from hr_time.api import logger
from hr_time.api.check_in.event import CheckinEvent
from hr_time.api.flextime.repository import CheckinDuration


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

            # Cannot start with a non-brake OUT event
            if (not current.is_in) and (not current.is_brake):
                logger.info("Unable to match checkin event " + current.id)
                current = event
                continue

            # Matching OUT event to current IN event
            if current.is_in and (not current.is_brake):
                if not event.is_in:
                    durations.append(CheckinDuration.build_from_events(current, event))

                    if event.is_brake:
                        current = event
                    else:
                        current = None

                    continue
                else:
                    logger.info("Skipping double checkin event " + event.id)
                    continue

            # Currently in brake, searching for IN event
            if (not current.is_in) and current.is_brake:
                if event.is_in:
                    durations.append(CheckinDuration.build_from_events(current, event))
                    current = event

        return durations