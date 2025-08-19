// Copyright (c) 2024, AtlasAero GmbH and contributors
// For license information, please see license.txt

const WorklogHelpers = {
    /** Fetch and set HomeOffice value from the LocalStorage */
    restoreWfhPreference: function(frm) {
        const wfhPrefKey = HR_TIME?.LS_KEYS?.PREV_WFH_PREF || 'neo_hr_time_last_wfh_value';
        const wfhPref = localStorage.getItem(wfhPrefKey);
        
        if (wfhPref !== null) {
            frm.set_value('is_home_office', wfhPref);
        }
    },

    /** Set placeholders for fields */
    localizePlaceholders: function(frm){
        Object.values(frm.fields_dict).forEach(field => {
            if (field.df && field.df.placeholder) {
                field.df.placeholder = frappe._(field.df.placeholder);
                field.refresh();  // Refresh UI so the new placeholder shows up
            }
        })
    },

    /** Event handler to set employee field's text hint with employee's name when that employee option is selected */
    setupEmployeeSelectionHint: function(frm) {
        if (frm.employeeSelectionSetup) return;
        
        frm.employeeSelectionSetup = true;

        $(frm.wrapper).on('click', 'ul[role="listbox"] div[role="option"]', (e) => {
            const employeeField = frm.fields_dict.employee;
            if (!employeeField) return;
            
            const wrapper = employeeField.wrapper;
            const optionDiv = e.currentTarget;
            const empName = optionDiv.querySelector('span.small')?.textContent;
            const helpBox = wrapper.querySelector('p.help-box');
            
            if (empName && helpBox) {
                helpBox.textContent = empName;
            }
        });
    },

    /** Auto set employee field by clicking the first option in the Employee select field */
    attemptAutoSelectEmployee: function(employeeField, frm) {
        if(frm.doc.employee) return;

        const wrapper = employeeField.wrapper;
        let attempts = 0;
        const maxAttempts = 30; // Prevent infinite looping

        const attemptAutoSelect = setInterval(() => {
            attempts++;
            const firstOption = wrapper.querySelector('ul div:nth-child(1) p');
            const empNameSpan = firstOption?.querySelector('span.small');
            const empTitle = firstOption?.getAttribute('title');

            if (firstOption && empNameSpan && empTitle) {
                clearInterval(attemptAutoSelect);
                frm.set_value('employee', empTitle);

                const helpBox = wrapper.querySelector('p.help-box');
                if (helpBox) helpBox.textContent = empNameSpan.textContent;
                
                const btnNow =  document.querySelector(".datepicker--button[data-action='today']")
                if(btnNow) btnNow.click();
                
                const taskDescEditor = frm.fields_dict.task_desc?.$wrapper
                    .get(0)
                    .querySelector('.ql-editor');

                if (taskDescEditor) {
                    taskDescEditor.focus();
                }
            } else if (attempts >= maxAttempts){
                clearInterval(attemptAutoSelect)
            }
        }, 200); // Check if Options loaded every 200ms
    },
};

frappe.ui.form.on('Worklog', {
    
    onload: function(frm) {
        WorklogHelpers.restoreWfhPreference(frm);
        WorklogHelpers.localizePlaceholders(frm);
    },

    /** Update 'Home Office' preference in localStorage before saving worklog */
    before_save: function(frm) {
        try{
            // Saving Home office preference
            if (frm.doc.is_home_office != null && frm.doc.is_home_office !== ''){
                const prevWfhPref = HR_TIME?.LS_KEYS?.PREV_WFH_PREF || 'neo_hr_time_last_wfh_value'
                localStorage.setItem(prevWfhPref, frm.doc.is_home_office.toString());
            }
        }catch (error){
            console.error('Failed to save WFH preference:', error)
        }
    },

    refresh: function (frm) {
        WorklogHelpers.setupEmployeeSelectionHint(frm);

        const employeeField = frm.fields_dict.employee;
        if (!employeeField) return;

        WorklogHelpers.attemptAutoSelectEmployee(employeeField, frm);
    },
    /** 
     * Validate the Worklog form and display user-friendly warnings
     * Prevents submission if critical fields are missing/invalid
     */
    validate: function(frm) {
        const { employee, log_time, is_home_office } = frm.doc;
        const errors = [];
        const errorFields = {};

        // Validate required fields (always check these)
        if (!employee) {
            errors.push(__("Employee ID is required"));
            errorFields.employee = true;
        }
        
        if (is_home_office === null || is_home_office === "") {
            errors.push(__("Please specify Home Office status"));
            errorFields.is_home_office = true;
        }

        // Only validate log_time if it exists
        if (log_time) {
            if (new Date(log_time) > new Date()) {
                errors.push(__("The entered time cannot be in the future"));
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
            frappe.msgprint({
                title: __('Validation Errors'),
                message: errors.join('<hr>'),
                indicator: 'orange'
            });
            frappe.validated = false;
        }

        return errors.length === 0;
    }
});