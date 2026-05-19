from enum import Enum


class LogType(Enum):
    """Check-in/out log type for database"""
    IN = "IN"
    OUT = "OUT"


class Action(Enum):
    """Check-in actions (UI and service)"""
    START_WORK = "Start of work"
    BREAK = "Break"
    RESUME_WORK = "Resume work"
    END_WORK = "End of work"

    @classmethod
    def from_string(cls, value: str):
        """Convert string to Action enum"""
        for action in cls:
            if action.value == value:
                return action
        return None


class State(Enum):
    """Internal check-in state"""
    UNKNOWN = "UNKNOWN"
    IN = "IN"
    BREAK = "BREAK"
    OUT = "OUT"
