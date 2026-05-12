import json

import frappe

from hr_time.api.worklog.domain.task.repository import TaskRepository


@frappe.whitelist()
def task_query_with_assignment(doctype, txt, searchfield, start, page_length, filters, reference_doctype=None):
    """Custom task query that filters by user assignment using JSON_CONTAINS."""

    user_id = frappe.session.user

    # Parse filters from the request (they come as JSON string)
    if isinstance(filters, str):
        filters = json.loads(filters)

    # Extract excluding task names from filters
    excluded_tasks = []
    if filters and filters.get("name") and filters["name"][0] == "not in":
        excluded_tasks = filters["name"][1]

    # Extract excluded statuses from filters
    excluded_statuses = []
    if filters and filters.get(TaskRepository.FIELD_STATUS) and filters[TaskRepository.FIELD_STATUS][0] == "not in":
        excluded_statuses = filters[TaskRepository.FIELD_STATUS][1]

    # Main query with exact assignment matching
    query = f"""
        SELECT name, subject
        FROM `tab{TaskRepository.DOCTYPE_NAME}`
        WHERE
            docstatus < 2  -- Not cancelled/archived
            AND (
                JSON_CONTAINS({TaskRepository.FIELD_ASSIGN}, %s)
                OR {TaskRepository.FIELD_IS_GENERIC} = 1  -- Include generic tasks by default without assignment
            )
            AND ({TaskRepository.FIELD_IS_INTERNAL} != 1 OR {TaskRepository.FIELD_IS_INTERNAL} IS NULL)
    """
    params = [f'"{user_id}"']

    # Add excluded tasks condition
    if excluded_tasks:
        placeholders = ', '.join(['%s'] * len(excluded_tasks))
        query += f" AND name NOT IN ({placeholders})"
        params.extend(excluded_tasks)

    # Add excluded statuses condition
    if excluded_statuses:
        placeholders = ', '.join(['%s'] * len(excluded_statuses))
        query += f" AND {TaskRepository.FIELD_STATUS} NOT IN ({placeholders})"
        params.extend(excluded_statuses)

    # Add search condition
    if txt:
        query += f" AND ({searchfield} LIKE %s OR {TaskRepository.FIELD_SUBJECT} LIKE %s)"
        params.extend([f'%{txt}%', f'%{txt}%'])

    # Add pagination
    query += f" LIMIT %s OFFSET %s"
    params.extend([page_length, start])

    # Execute query and return results
    results = frappe.db.sql(query, params)
    return results or []
