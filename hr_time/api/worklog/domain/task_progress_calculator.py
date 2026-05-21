"""
Pure domain calculator for task progress.
NO Frappe imports, NO repositories, NO database calls.
"""


class TaskProgressCalculator:
    """
    Pure domain service for task progress calculations.
    All methods are stateless and have no external dependencies.
    """

    @staticmethod
    def calculate_progress_increment(time_spent: float, expected_time: float) -> float:
        """
        Calculate progress percentage for a single task allocation.

        Args:
            time_spent: Hours spent on the task in this session
            expected_time: Total expected hours for the task

        Returns:
            Progress percentage (0-100)
        """
        if expected_time <= 0 or time_spent <= 0:
            return 0.0
        increment = (time_spent / expected_time) * 100
        return round(min(increment, 100), 1)

    @staticmethod
    def calculate_total_progress(total_hours: float, expected_time: float) -> float:
        """
        Calculate total progress percentage from cumulative hours.

        Args:
            total_hours: Total hours spent on task (all sessions)
            expected_time: Total expected hours for the task

        Returns:
            Progress percentage (0-100)
        """
        if expected_time <= 0:
            return 0.0
        progress = (total_hours / expected_time) * 100
        return min(progress, 100)

    @staticmethod
    def should_update_progress(current_progress: float, new_progress: float, epsilon: float = 0.01) -> bool:
        """
        Determine if progress should be updated based on change threshold.

        Args:
            current_progress: Current progress percentage
            new_progress: Newly calculated progress percentage
            epsilon: Minimum change threshold (default 0.01%)

        Returns:
            True if update is needed, False otherwise
        """
        return abs(new_progress - current_progress) > epsilon

    @staticmethod
    def calculate_row_progress_increment(time_spent: float, expected_time: float) -> float:
        """
        Calculate progress increment for a worklog task row.

        Args:
            time_spent: Hours spent in this worklog entry
            expected_time: Total expected hours for the task

        Returns:
            Progress increment percentage (0-100)
        """
        if not expected_time or expected_time <= 0:
            return 0.0
        if not time_spent or time_spent <= 0:
            return 0.0
        return min((time_spent / expected_time) * 100, 100)
