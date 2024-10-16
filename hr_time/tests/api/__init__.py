import sys
from types import SimpleNamespace
from typing import Optional
from unittest.mock import MagicMock


class FakeLogger:
    @staticmethod
    def info(message):
        return

    def set_log_level(self, level):
        return

    @staticmethod
    def error(message, args=None):
        return


class FakeDB:
    @staticmethod
    def commit():
        FakeLogger.info("DB Commit")

    @staticmethod
    def rollback():
        FakeLogger.error("DB Rollback")


class FakeUtils:
    logger = FakeLogger()


class FakeDocument(SimpleNamespace):
    """
    A mock document class that mimics Frappe's document behavior, including the save() method.
    """

    def save(self):
        # Simulate saving the document (do nothing or add custom logic if needed)
        return


class FakeFrappe(object):
    utils = FakeUtils()
    db = FakeDB()

    class User:
        def __init__(self, email):
            self.doc = MagicMock()
            self.doc.email = email

    @staticmethod
    def get_user():
        return FakeFrappe.User(email='test.user@example.com')

    @staticmethod
    def throw(message, error_type):
        raise error_type(message)

    @staticmethod
    def get_current():
        # Mock get_user to return a user object with an email
        mock_user = MagicMock()
        mock_user.doc.email = 'test.user@example.com'
        # Set return value for frappe.get_user()
        return mock_user

    @staticmethod
    def logger(level, allow_site, file_count):
        return FakeLogger()

    # Simulating frappe whitelist function
    @staticmethod
    def whitelist():
        # Return a no-op decorator that simply returns the function passed to it
        return lambda func: func

    @staticmethod
    def _(text):
        # A simple translation function for mock
        return text

    @staticmethod
    def get_all(doctype, fields=None, filters=None):
        if doctype == "Worklog":
            if filters:
                if filters.get('employee_id') == "001":
                    return [
                        FakeDocument(name="Test Employee", employee="001",
                                     task_desc="test description", task="Task A"),
                        FakeDocument(name="Test Employee", employee="001",
                                     task_desc="test description", task="Task B"),
                    ]
                elif filters.get('employee_id') == "002":
                    return []
            else:
                return []
        return []

    @staticmethod
    def new_doc(doctype):
        if doctype == "Worklog":
            return FakeDocument(name="NEW_WORKLOG", employee=None, task_desc=None, task=None)
        raise AttributeError(f"Unknown doctype: {doctype}")

    @staticmethod
    def get_hooks(hook_name):
        # Return a mock response for hooks
        # You can customize the return value based on the tests you're running
        return {
            # This simulates the behavior of the actual `frappe.get_hooks`
            "persistent_cache_keys": []
        }.get(hook_name, [])

    class DoesNotExistError(Exception):
        pass


# noinspection PyTypeChecker
sys.modules["frappe"] = FakeFrappe
