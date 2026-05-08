from hr_time.api.worklog.domain.entities import WorklogState


class WorklogStateService:
    """Domain service for determining worklog state"""

    @staticmethod
    def determine_state(
        is_new_doc: bool,
        is_todays: bool,
        has_open_session: bool,
        on_break: bool
    ) -> WorklogState:
        """Determine worklog state from context"""
        if is_new_doc:
            return WorklogState.NEW
        elif not is_todays:
            return WorklogState.HISTORICAL
        elif has_open_session:
            return WorklogState.WORKING
        elif on_break:
            return WorklogState.ON_BREAK
        else:
            return WorklogState.COMPLETED

    @staticmethod
    def is_editable(state: WorklogState, is_new_doc: bool, is_todays: bool) -> bool:
        """Determine if worklog is editable"""
        if is_new_doc:
            return True
        elif is_todays and (state == WorklogState.WORKING or state == WorklogState.ON_BREAK):
            return True
        return False
