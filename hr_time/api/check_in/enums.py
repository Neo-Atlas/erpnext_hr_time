from enum import Enum


class LogType(Enum):
    """Check-in/out log type"""
    IN = "IN"
    OUT = "OUT"

    @classmethod
    def from_string(cls, value: str) -> 'LogType':
        """Convert string to LogType"""
        if value == "IN":
            return cls.IN
        elif value == "OUT":
            return cls.OUT
        raise ValueError(f"Invalid log type: {value}")

    def to_string(self) -> str:
        return self.value
