from enum import Enum


class DocumentStatus(Enum):
    """Standard document status across all doctypes"""
    DRAFT = 0
    SUBMITTED = 1
    CANCELLED = 2

    @classmethod
    def from_value(cls, value: int) -> 'DocumentStatus':
        """Get enum from integer value"""
        for status in cls:
            if status.value == value:
                return status
        return cls.DRAFT

    def is_draft(self) -> bool:
        return self == DocumentStatus.DRAFT

    def is_submitted(self) -> bool:
        return self == DocumentStatus.SUBMITTED

    def is_cancelled(self) -> bool:
        return self == DocumentStatus.CANCELLED
