"""
Utility Module for Displaying User Messages and Raising Errors in Frappe Framework
"""

import frappe
from frappe import _


def warn_user(msg):
    """
    Display a closable warning message on top of the screen.
    """
    frappe.msgprint(
        title=_("Warning"),
        message=_(msg),
        indicator="orange"
    )


def alert_info(msg):
    """
    Show an informational message as a brief toast alert.
    """
    frappe.show_alert(
        title=_("Message"),
        message=_(msg),
        indicator="blue"
    )


def alert_success(msg):
    """
    Show a success message as a brief alert.
    """
    frappe.show_alert(
        title=_("Success"),
        message=_(msg),
        indicator="green"
    )


def alert_failure(msg):
    """
    Show a failure message as a brief alert.
    """
    frappe.show_alert(
        title=_("Failure"),
        message=_(msg),
        indicator="red"
    )


def throw_error_msg(msg, error_type=Exception):
    """
    Raise an exception with the given error message, with an optional error type.

    Args:
        msg (str): The error message to raise.
        error_type (Exception): The type of exception to raise (default is Exception).
    """
    frappe.throw(_(msg), error_type)
