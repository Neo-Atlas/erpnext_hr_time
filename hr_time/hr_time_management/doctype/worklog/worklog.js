// Copyright (c) 2024, AtlasAero GmbH and contributors
// For license information, please see license.txt

const PREV_WFH_PREF_KEY = HR_TIME?.LS_KEYS?.PREV_WFH_PREF || 'neo_hr_time_last_wfh_value';

const WorklogHelpers = {
    /** Fetch and set HomeOffice value from the LocalStorage */
    restoreWfhPreference: function(frm) {
        const wfhPref = JsUtils.getStringFromLocalStore(PREV_WFH_PREF_KEY);
        if (wfhPref) {
            frm.set_value('is_home_office', wfhPref);
        }
    },

    /** Set translated placeholders for fields */
    localizePlaceholders: function(frm){
        Object.values(frm.fields_dict).forEach(field => {
            if (field.df && field.df.placeholder) {
                field.df.placeholder = frappe._(field.df.placeholder);
                field.refresh();
            }
        })
    },

    /** Function to set employee field's text hint with employee's name */
    setEmployeeNameHint: function(frm, fullName) {
        const employeeField = frm.fields_dict.employee;
        if (!employeeField) return;
        
        const wrapper = employeeField.wrapper;
        const helpBox = wrapper.querySelector('p.help-box');
        
        if (helpBox) {
            helpBox.textContent = fullName;
        }
    },

    /**
     * Focuses on the first empty field based on fixed priority.
     * @returns {boolean} - whether a field was focused
     */
    focusOnAnEmptyField: function(frm){
        const fieldPriority = [  // Field focus priority (which aren't auto filled)
                'task_desc',
                'task',
                'ticket_link'
            ]
        
        for(const fieldname of fieldPriority){
            const field = frm.fields_dict[fieldname]
            if(!field) continue;

            const value = frm.doc[fieldname]
            if(value === null || value === undefined || value === ''){
                this.focusOnField(field);
                return true
            }
        }
        return false;
    },

    /** Focus on a field (based on field type) */
    focusOnField: function(field) {
        // Different focus methods for different field types
        if (field.df.fieldtype === 'Text Editor' || field.df.fieldtype === 'Text') {
            const editor = field.$wrapper
                .get(0)
                .querySelector('.ql-editor, textarea, input');  // For text editor fields
            
            if (editor) {
                editor.focus();
            }
        } else if (field.$input && field.$input.length > 0) {
            field.$input.focus();  // For other input fields
        }
    },

    /** Fetch and auto set the fields :
     * - employee: the current employee filling the Worklog along with the field's hint element with full name.
     * - log_time: the current time in DB format
     *      - and focus on the first field which is empty (or on 'task description' otherwise)
     */
    autoPopulateNewWorklogFields: function(frm){
        try{
            // 1. Fetch and set `employee` and `full_name` hint text.
            FlextimeApi.fetchCurrentEmployee()
                        .then(employee => {
                            frm.set_value('employee', employee?.id);
                            WorklogHelpers.setEmployeeNameHint(frm, employee?.full_name)
                        })
                        .catch(err => {
                            frappe.throw(err.message);
                        });

            // 2. Set log time to current time in DB format by default
            const dbFormattedDateTime = FrappeUtils.get_db_format_time(new Date())
            frm.set_value("log_time", dbFormattedDateTime);
        } catch (error) {
            frappe.throw(error.message);            
        } finally {
            let isFieldFocused = this.focusOnAnEmptyField(frm)            
            if(!isFieldFocused){
                // focus on the 'Task desc' by default if no field is focused
                const taskDesc = frm.fields_dict['task_desc']
                this.focusOnField(taskDesc)
            }
        }
    }
};

frappe.ui.form.on('Worklog', {

    onload: function(frm) {
        WorklogHelpers.localizePlaceholders(frm);
        WorklogHelpers.restoreWfhPreference(frm);
    },

    /** Update 'Home Office' preference in localStorage before saving worklog */
    before_save: function(frm) {
        if (['Yes', 'No'].includes(frm.doc.is_home_office)){
            JsUtils.saveStringToLocalStore(PREV_WFH_PREF_KEY, frm.doc.is_home_office);
        }
    },

    refresh: function (frm) {
        const employeeField = frm.fields_dict.employee;
        if (!employeeField) return;

        if(!frm.doc.employee){  // Refill fields for new form (i.e. if employee field is empty)
            WorklogHelpers.autoPopulateNewWorklogFields(frm)
        }
    },

    /** 
     * Validate the Worklog document's required fields and display user-friendly warnings
     * Prevents submission if critical fields are missing/invalid
     */
    validate: function(frm) {
        const { employee, log_time, is_home_office } = frm.doc;
        const errors = [];
        const errorFields = {};

        if (!employee) {
            errors.push(__(MESSAGES.WARN_NO_EMP_ID));
            errorFields.employee = true;
        }
        
        if (is_home_office === null || is_home_office === "") {
            errors.push(__(MESSAGES.WARN_NO_HOME_OFFICE));
            errorFields.is_home_office = true;
        }

        if (log_time) {
            if (new Date(log_time) > new Date()) {  // If log_time exists, check if it is in future
                errors.push(__(MESSAGES.ERR_LOG_IN_FUTURE));
                errorFields.log_time = true;
            }
        }

        // Highlight error fields
        Object.keys(errorFields).forEach(fieldname => {
            const inputField =  document.querySelector(`.frappe-control[data-fieldname=${fieldname}]`)
                
            if(inputField){
                inputField.classList.add('has-error');
            }
        });

        // Show all errors at once if any exist
        if (errors.length > 0) {
            FrappeUtils.warn_user(errors.join('<hr>'))
            frappe.validated = false;
        }

        return errors.length === 0;
    }
});