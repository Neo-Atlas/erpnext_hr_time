import frappe


class FrappeUtils:
    """
    server-side utility class with (wrapper) methods for Frappe's messaging methods - to display (translatable)
    alerts and messages in the application.
    """

    @staticmethod
    def error_modal(msg, title="Error"):
        frappe.msgprint(frappe._(msg), title=frappe._(title), indicator="red")

    @staticmethod
    def success_modal(msg, title="Success"):
        frappe.msgprint(frappe._(msg), title=frappe._(title), indicator="green")

    @staticmethod
    def info_modal(msg, title="Info"):
        frappe.msgprint(frappe._(msg), title=frappe._(title), indicator="blue")

    @staticmethod
    def warn_user(msg):
        frappe.msgprint(frappe._(msg), title=frappe._("Warning"), indicator="orange")

    @staticmethod
    def throw_error_msg(msg, error_type=Exception):
        """
        Raise an exception with the given error message, with an optional error type.

        Args:
            msg (str): The error message to raise.
            error_type (Exception): The type of exception to raise (default is Exception).
        """
        frappe.throw(frappe._(msg), error_type)
