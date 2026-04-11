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
     * Fetches the current employee document object by calling the backend API.
     * 
     * @returns {Promise<object>} A promise that resolves with the employee document or rejects with an error message.
     */
    static fetchCurrentEmployee = () => {
        return new Promise((resolve, reject) => {
            frappe.call({
                method: "hr_time.api.employee.api.get_current_employee",
                callback: (response) => {
                    // console.log('response: ',response);
                    
                    const employee = response.message;
                    if (employee) {
                        resolve(employee); // Resolve with the employee
                    } else {
                        reject(new Error(MESSAGES.NOT_FOUND_EMPLOYEE));
                    }
                },
                error: (error) => {
                    reject(error); // Handle API errors
                },
            });
        });
    }
}