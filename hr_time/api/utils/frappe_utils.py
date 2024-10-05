import frappe
# from frappe import show_alert, msgprint
try:
    from frappe import _
except ImportError:
    # Fallback if _ isn't available (for tests)
    def _(text): return text

# Warn the user with an orange indicator


def warn_user(msg):
    frappe.msgprint(
        title=_("Warning"),
        message=_(msg),
        indicator="orange"
    )


# Show an informational message (similar to alert)
def alert_info(msg):
    frappe.show_alert(
        title=_("Message"),
        message=_(msg),
        indicator="blue"
    )


# Show a success alert
def alert_success(msg):
    frappe.show_alert(
        title=_("Success"),
        message=_(msg),
        indicator="green"
    )

# Show a failure alert


def alert_failure(msg):
    frappe.show_alert(
        title=_("Failure"),
        message=_(msg),
        indicator="red"
    )
