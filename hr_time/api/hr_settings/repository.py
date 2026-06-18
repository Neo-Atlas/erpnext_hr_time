from typing import Optional

import frappe

from hr_time.api.worklog.domain.task.repository import TaskRepository


class HRDefaults:
    TOLERANCE_MINUTES = 0
    ACTIVITY_TYPE = "Task"
    BUFFER_TASK_SUBJECT = "Worklog Buffer"


class HRSettingsRepository:
    CACHE_KEY = "hr_settings"
    DOCTYPE_NAME = "HR Settings"

    FIELD_NAME_TOLERANCE = "custom_worklog_time_allocation_tolerance"
    _KEY_TOLERANCE = "tolerance_minutes"
    _DEFAULT_TOLERANCE = HRDefaults.TOLERANCE_MINUTES

    _FIELD_NAME_ACTIVITY_TYPE = "custom_default_timesheet_activity_type"
    _KEY_ACTIVITY_TYPE = "default_activity_type"
    _DEFAULT_ACTIVITY_TYPE = HRDefaults.ACTIVITY_TYPE

    _FIELD_NAME_BUFFER_TASK = "custom_worklog_buffer_task"
    _KEY_BUFFER_TASK = "buffer_task"
    _DEFAULT_BUFFER_TASK_SUBJECT = HRDefaults.BUFFER_TASK_SUBJECT

    # ---------- Internal Helpers ----------
    @staticmethod
    def _cache_hget(key: str, field: str) -> Optional[str]:
        return frappe.cache().hget(key, field)

    @staticmethod
    def _cache_hset(key: str, field: str, value) -> None:
        frappe.cache().hset(key, field, value)

    @staticmethod
    def _get_cached_int(field_key: str) -> Optional[int]:
        cached = HRSettingsRepository._cache_hget(
            HRSettingsRepository.CACHE_KEY, field_key
        )
        if cached is not None:
            try:
                return int(cached)
            except (ValueError, TypeError):
                return None
        return None

    @staticmethod
    def _get_cached_str(field_key: str) -> Optional[str]:
        cached = HRSettingsRepository._cache_hget(
            HRSettingsRepository.CACHE_KEY, field_key
        )
        return cached if cached is not None else None

    # ---------- Public API ----------

    @staticmethod
    def get_tolerance_minutes() -> int:
        cached = HRSettingsRepository._get_cached_int(
            HRSettingsRepository._KEY_TOLERANCE
        )
        if cached is not None:
            return cached

        value = frappe.db.get_single_value(
            HRSettingsRepository.DOCTYPE_NAME,
            HRSettingsRepository.FIELD_NAME_TOLERANCE
        )

        value = int(value) if value is not None else HRSettingsRepository._DEFAULT_TOLERANCE

        HRSettingsRepository._cache_hset(
            HRSettingsRepository.CACHE_KEY,
            HRSettingsRepository._KEY_TOLERANCE,
            value
        )

        return value

    @staticmethod
    def get_default_activity_type() -> str:
        cached = HRSettingsRepository._get_cached_str(
            HRSettingsRepository._KEY_ACTIVITY_TYPE
        )
        if cached is not None:
            return cached

        value = frappe.db.get_single_value(
            HRSettingsRepository.DOCTYPE_NAME,
            HRSettingsRepository._FIELD_NAME_ACTIVITY_TYPE
        ) or HRSettingsRepository._DEFAULT_ACTIVITY_TYPE

        value = value or HRSettingsRepository._DEFAULT_ACTIVITY_TYPE

        HRSettingsRepository._cache_hset(
            HRSettingsRepository.CACHE_KEY,
            HRSettingsRepository._KEY_ACTIVITY_TYPE,
            value
        )

        return value

    @staticmethod
    def get_buffer_task() -> str:
        cached = HRSettingsRepository._get_cached_str(
            HRSettingsRepository._KEY_BUFFER_TASK
        )
        if cached is not None:
            return cached

        task_id = frappe.db.get_single_value(
            HRSettingsRepository.DOCTYPE_NAME,
            HRSettingsRepository._FIELD_NAME_BUFFER_TASK
        )

        if not task_id:
            task_id = TaskRepository.create_buffer_task(
                HRSettingsRepository._DEFAULT_BUFFER_TASK_SUBJECT
            )
            frappe.db.set_single_value(
                HRSettingsRepository.DOCTYPE_NAME,
                HRSettingsRepository._FIELD_NAME_BUFFER_TASK,
                task_id
            )

        HRSettingsRepository._cache_hset(
            HRSettingsRepository.CACHE_KEY,
            HRSettingsRepository._KEY_BUFFER_TASK,
            task_id
        )

        return task_id

    @staticmethod
    def clear_cache(doc=None, method=None) -> None:
        frappe.cache().delete_value(
            HRSettingsRepository.CACHE_KEY
        )
