import frappe
from frappe import _


class FrappeUtils:
    """
    Utility class with (wrapper) methods for Frappe's messaging methods - to display (translatable)
    alerts and messages in the application.
    """

    @staticmethod
    def warn_user(msg):
        """
        Display a closable warning message on top of the screen.
        """
        frappe.msgprint(
            title=_("Warning"),
            message=_(msg),
            indicator="orange"
        )

    @staticmethod
    def throw_error_msg(msg, error_type=Exception):
        """
        Raise an exception with the given error message, with an optional error type.

        Args:
            msg (str): The error message to raise.
            error_type (Exception): The type of exception to raise (default is Exception).
        """
        frappe.throw(_(msg), error_type)
