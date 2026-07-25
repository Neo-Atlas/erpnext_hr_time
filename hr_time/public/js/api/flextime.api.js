/**
 * @fileoverview Utility class with service functions for fetching employee-related data.
 * @module HR_TIME_MANAGEMENT
 */

/**
 * A utility class for interacting with the backend to retrieve employee-related data.
 */
export class FlextimeApi{
    /**
     * Fetches the current employee ID by calling the backend API.
     * 
     * @returns {Promise<string>} A promise that resolves with the employee ID or rejects with an error message.
     */
    static fetchCurrentEmployeeId = () => {
        return new Promise((resolve, reject) => {
            frappe.call({
                method: API.EMPLOYEE.GET_CURRENT_EMPLOYEE_ID,
                callback: (response) => {
                    if (response.message && typeof response.message === 'string') {
                        resolve(response.message);  // Valid employee ID
                    } else if (response.message === null || response.message === undefined) {
                        console.warn('user is Admin');
                        resolve(null);  // No employee (admin user) - resolve with null
                    }else {
                        reject(new Error("No employee ID returned"));
                    }
                },
                error: (error) => {
                    reject(new Error(error.message || MESSAGES.ERR_BACKEND_UNREACHABLE));
                },
            });
        });
    }

    /**
     * Fetches the current employee document object by calling the backend API.
     * 
     * @returns {Promise<object>} A promise that resolves with the employee document or rejects with an error message.
     */
    static fetchCurrentEmployee = () => {
        return new Promise((resolve, reject) => {
            frappe.call({
                method: API.EMPLOYEE.GET_CURRENT_EMPLOYEE,
                callback: (response) => {
                    const result = response.message;
                    
                    if (response && response.message && typeof response.message === 'object') {
                        resolve(response.message); // Employee document
                    } else if (response.message === null || response.message === undefined) {
                        reject(new Error(result.message)); // Backend message
                    } else {
                        reject(new Error(MESSAGES.ERR_UNEXPECTED_RESPONSE));
                    }
                },
                error: (error) => {
                    reject(new Error(MESSAGES.ERR_BACKEND_UNREACHABLE));
                },
            });
        });
    }
}