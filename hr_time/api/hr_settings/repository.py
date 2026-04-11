import frappe


class HRSettingsRepository:
    CACHE_KEY = "hr_settings"
    _DOCTYPE_NAME = "HR Settings"
    _FIELD_NAME_TOLERANCE = "cstm_worklog_time_allocation_tolerance"
    _KEY_TOLERANCE = "tolerance_minutes"
    _DEFAULT_TOLERANCE = 30
    _FIELD_NAME_ACTIVITY_TYPE = "cstm_default_timesheet_activity_type"
    _KEY_ACTIVITY_TYPE = "default_activity_type"
    _DEFAULT_ACTIVITY_TYPE = "Task"
    _FIELD_NAME_BUFFER_TASK = "cstm_worklog_buffer_task"
    _KEY_BUFFER_TASK = "buffer_task"
    _DEFAULT_BUFFER_TASK = "Worklog Buffer"
    
    @staticmethod
    def get_tolerance_minutes() -> int:
        cached = frappe.cache().hget(
            HRSettingsRepository.CACHE_KEY,
            HRSettingsRepository._KEY_TOLERANCE
        )
        if cached is not None:
            return cached
        
        value = frappe.db.get_single_value(
            HRSettingsRepository._DOCTYPE_NAME,
            HRSettingsRepository._FIELD_NAME_TOLERANCE
        ) or HRSettingsRepository._DEFAULT_TOLERANCE
        
        frappe.cache().hset(
            HRSettingsRepository.CACHE_KEY,
            HRSettingsRepository._KEY_TOLERANCE,
            value
        )
        return value
    
    @staticmethod
    def get_default_activity_type() -> str:
        cached = frappe.cache().hget(
            HRSettingsRepository.CACHE_KEY,
            HRSettingsRepository._KEY_ACTIVITY_TYPE
        )
        if cached is not None:
            return cached
        
        value = frappe.db.get_single_value(
            HRSettingsRepository._DOCTYPE_NAME,
            HRSettingsRepository._FIELD_NAME_ACTIVITY_TYPE
        ) or HRSettingsRepository._DEFAULT_ACTIVITY_TYPE
        
        frappe.cache().hset(
            HRSettingsRepository.CACHE_KEY,
            HRSettingsRepository._KEY_ACTIVITY_TYPE,
            value
        )

        return value
    
    @staticmethod
    def get_buffer_task() -> str:
        print('get_buffer_task')
        cached = frappe.cache().hget(
            HRSettingsRepository.CACHE_KEY,
            HRSettingsRepository._KEY_BUFFER_TASK
        )
        if cached is not None:
            print('from cache')
            return cached
        
        task_id = frappe.db.get_single_value(
            HRSettingsRepository._DOCTYPE_NAME,
            HRSettingsRepository._FIELD_NAME_BUFFER_TASK
        )

        if not task_id:
            # Create the default buffer task
            task = frappe.new_doc("Task")
            task.subject = HRSettingsRepository._DEFAULT_BUFFER_TASK
            task.status = "Open"
            task.is_generic = 1
            task.insert(ignore_permissions=True)
            task_id = task.name

        frappe.cache().hset(
            HRSettingsRepository.CACHE_KEY,
            HRSettingsRepository._KEY_BUFFER_TASK,
            task_id
        )
    
        print('inside get_buffer_task')
        print(task_id)
        return task_id
    
    @staticmethod
    def clear_cache():
        frappe.cache().hdel(
            HRSettingsRepository.CACHE_KEY
        )
