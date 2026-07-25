import frappe

from hr_time.api.check_in.enums import State


class CheckinDisplayService:
    """Maps domain State to presentation values"""

    @staticmethod
    def get_display_data(state: State) -> dict:
        """Get display data for frontend templates and APIs"""
        mapping = {
            State.IN: {
                "label": frappe._("Checked in"),
                "status": "work",
                "icon": "check"
            },
            State.OUT: {
                "label": frappe._("Checked out"),
                "status": "out",
                "icon": "remove"
            },
            State.BREAK: {
                "label": frappe._("Break"),
                "status": "break",
                "icon": "coffee"
            },
            State.UNKNOWN: {
                "label": frappe._("Unknown"),
                "status": "out",
                "icon": "question"
            }
        }
        return mapping.get(state, mapping[State.UNKNOWN])
