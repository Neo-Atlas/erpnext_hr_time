"""
HR Time Management API Package
"""

import sys

# Only import frappe when actually running in Frappe environment
if 'bench' in sys.argv or 'frappe' in sys.modules:
    import frappe
    frappe.utils.logger.set_log_level("DEBUG")
    logger = frappe.logger("hr_time", allow_site=True, file_count=50)
else:
    # Running in CI or standalone
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("hr_time")
