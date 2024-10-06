/**
 * @fileoverview Service functions for fetching employee-related data.
 * @module HR_TIME_MANAGEMENT
 */


import MESSAGES from "../constants/messages.json";

/**
 * Fetchse the current employee ID by calling the backend API.
 * 
 * @returns {Promise<string>} A promise that resolves with the employee ID or rejects with an error message.
 */
const fetchCurrentEmployeeId = () => {
    return new Promise((resolve, reject) => {
        frappe.call({
            method: "hr_time.api.employee.api.get_current_employee_id",
            callback: (response) => {
                const employee_id = response.message;
                if (employee_id) {
                    resolve(employee_id); // Resolve with the employee ID
                } else {
                    reject(new Error(MESSAGES.NOT_FOUND_EMPLOYEE_ID));
                }
            },
            error: (error) => {
            reject(error); // Handle API errors
            },
        });
    });
}


/**
 * Fetches the worklog status (i.e. if employee has created worklog "today").
 * 
 * @param {string} employee_id - The ID of the employee whose worklog status is to be fetched.
 * @returns {Promise<boolean>} A promise that resolves with the worklog status (true / false) or rejects with an error.
 */
const fetchWorklogStatus = (employee_id) => {
    return new Promise((resolve, reject) => {
        frappe.call({
            method: "hr_time.api.worklog.api.has_employee_made_worklogs_today",
            args: { employee_id: employee_id },
            callback: (response) => {
                if (response && response.message !== undefined) {
                    resolve(response.message); // Resolve with the worklog status
                } else {
                    reject(new Error(MESSAGES.ERR_GET_WORKLOG_STATUS));
                }
            },
            error: (error) => {
                reject(error); // Handle API errors
            },
        });
    });
}

export {fetchCurrentEmployeeId, fetchWorklogStatus}