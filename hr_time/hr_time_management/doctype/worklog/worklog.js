// Copyright (c) 2024, AtlasAero GmbH and contributors
// For license information, please see license.txt

const PREV_WFH_PREF_KEY = HR_TIME?.LS_KEYS?.PREV_WFH_PREF || 'neo_hr_time_last_wfh_value';
let CACHED_TOLERANCE_MINUTES = null;
const LBL_BTN_SAVE_AND_CHECKOUT = __("Save & Checkout")
const DEFAULT_TOLERANCE_MINUTES = 0
const SHORT_INTERVAL_MS = 100

const DOCTYPE = {
  NAME:'Worklog', 
  CHILD: 'Worklog Tasks'
}

const FIELD = {
    TASK: 'task',
    SUBJECT: 'subject',
    EXPECTED_TIME: "expected_time",
    PRIORITY: "priority",
    TASK_DESC: "task_desc",
    STATUS: "status",
    LOG_TIME: "log_time",
    TIME_SAVED: "time_saved",
    TIME_SPENT: 'time_spent',
    IS_HOME_OFFICE: "is_home_office",
    TASKS_ENTRY: "tasks_entry",
    WORK_DESC: "work_desc",
    TICKET_LINK: "ticket_link",
    TIME_TOTAL_ACTUAL: "time_total_actual",
    TIME_SINCE_SAVE: "time_since_last_save",
    PROGRESS_INCREMENT: "progress_increment",
    WORKLOG_HEADLINE: "worklog_overview_headline",
    EXISTING_TASKS: "existing_tasks",
    PREFILLED_TASKS: "prefilled_tasks",
    HAS_OPEN_SESSION: "has_open_session"
    // ... etc
};

const WorklogHelpers = {
    /** Fetch and set HomeOffice value from the LocalStorage */
    restoreWfhPreference: function(frm) {
        // Only apply to new forms, not existing ones
        if (!frm.is_new()) return;

        const wfhPref = JsUtils.getStringFromLocalStore(PREV_WFH_PREF_KEY);
        if (wfhPref) {
            frm.set_value(FIELD.IS_HOME_OFFICE, wfhPref);
        }
    },

    /** Set translated placeholders for all fields */
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
                FIELD.WORK_DESC,
                FIELD.TICKET_LINK
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

    /** Format duration for display */
    formatDuration: function(hours) {
        const h = Math.floor(hours);
        const m = Math.round((hours - h) * 60);
        return `${h}h ${m}m`;
    },
};

function stop_work_duration_refresh(frm) {
    if (frm.work_duration_recalculation_interval) {
        clearInterval(frm.work_duration_recalculation_interval);
        frm.work_duration_recalculation_interval = null;
    }
}

function start_work_duration_refresh(frm) {
    // Clear any existing interval
    if (frm.work_duration_recalculation_interval) {
        clearInterval(frm.work_duration_recalculation_interval);
    }

    frm.work_duration_recalculation_interval = setInterval(() => {
        const isFullForm = frappe.get_route()[0] === 'Form' && frappe.get_route()[1] === DOCTYPE.NAME

        if(!isFullForm){
            stop_work_duration_refresh(frm)
            return
        }

        if (frm.doc.employee) {
            refresh_work_duration(frm);
        }
    }, window.WORK_DURATION_RECALC_INTERVAL_MS);
}

// Helper to refresh work duration
function refresh_work_duration(frm) {
    frappe.call({
        method: API.WORKLOG.PREPARE_CHECKOUT,
        args: { employee_id: frm.doc.employee },
        callback: function(r) {
            const data = r.message
            if (data) {
                // Update stored data on frm
                frm.worklog_data = data;
                frm.current_total = data[FIELD.TIME_TOTAL_ACTUAL];
                frm.time_since_last_save = data[FIELD.TIME_SINCE_SAVE];
                frm.set_value(FIELD.TIME_SAVED, data[FIELD.TIME_SAVED]);

                if (data[FIELD.WORKLOG_HEADLINE]) {
                    update_overview_headline(frm, data[FIELD.WORKLOG_HEADLINE], data.headline_color)
                }

                // Update allocation status below table
                recalculate_allocation_status(frm)

                // Update Save & Checkout button based on current state
                frm.remove_custom_button(LBL_BTN_SAVE_AND_CHECKOUT);
                if (data[FIELD.HAS_OPEN_SESSION] && !frm.read_only) {
                    frm.add_custom_button(LBL_BTN_SAVE_AND_CHECKOUT, () => {
                        save_and_checkout_action(frm);
                    });
                }
            }
        }
    });
}

frappe.ui.form.on(DOCTYPE.NAME, {

    onload: function(frm) {
        WorklogHelpers.localizePlaceholders(frm);
        WorklogHelpers.restoreWfhPreference(frm);
    },

    /** Update 'Home Office' preference in localStorage before saving worklog */
    before_save: function(frm) {
        if (frm.current_total) {
            frm.doc.__current_total = frm.current_total; // Store current total in a temporary field for backend use during save_and_checkout/refresh
        }        
        
        if (['Yes', 'No'].includes(frm.doc[FIELD.IS_HOME_OFFICE])){
            JsUtils.saveStringToLocalStore(PREV_WFH_PREF_KEY, frm.doc[FIELD.IS_HOME_OFFICE]);
        }
    },

    refresh: async function(frm) {
        
        // Reset ALL cached data when form loads
        frm.worklog_data = null;
        frm.worklog_context = null;
        frm.current_total = null;
        frm.time_since_last_save = null;
        frm.tolerance_minutes = null;

        // Set log_time for new forms
        if (frm.is_new() && !frm.doc[FIELD.LOG_TIME]) {
            frm.set_value(FIELD.LOG_TIME, FrappeUtils.get_db_format_time(new Date()));
        }

        // Clear any stale tasks for new forms
        if (frm.is_new() && frm.doc[FIELD.TASKS_ENTRY] && frm.doc[FIELD.TASKS_ENTRY].length > 0) {
            frm.clear_table(FIELD.TASKS_ENTRY);
            frm.refresh_field(FIELD.TASKS_ENTRY);
        }

        // STEP 1: Get worklog context (unified for all worklogs - new, existing, historical)        
        frappe.call({
            method: API.WORKLOG.GET_CONTEXT,
            args: {
                referred_worklog_name: frm.is_new() ? null : frm.doc.name,
                employee_id: frm.doc.employee
            },
            callback: function(r) {
                if (!r.message) return;

                const context = r.message;
                console.log('context: ',context);
                
                console.log('frm.doc.name: ',frm.doc.name);
                
                if (frm.is_new() && context.today_worklog_name && context.today_worklog_name !== frm.doc.name) {                    
                    FrappeUtils.toast_info(MESSAGES.INFO_OPENING_EXISTING, 3);
                    frappe.set_route('Form', DOCTYPE.NAME, context.today_worklog_name);
                    return;
                }

                frm.worklog_context = context;
                frm.tolerance_minutes = context.tolerance_minutes;
                
                // Set dashboard headline using pre-rendered HTML
                if (context[FIELD.WORKLOG_HEADLINE]) {
                    update_overview_headline(frm, context[FIELD.WORKLOG_HEADLINE])
                }
                
                // Set read-only state based on backend
                set_form_read_only(frm, context.is_read_only);
                
                // For historical worklogs, ensure no refresh runs
                if (frm.worklog_context.worklog_state === 'historical') {
                    if (frm.work_duration_recalculation_interval) {
                        stop_work_duration_refresh(frm);
                    }

                    // For read-only worklogs (historical/completed) hide the allocation indicator
                    const $container = frm.$wrapper.find('.allocation-mismatch-indicator');
                    if ($container.length) {
                        $container.empty();
                        $container.hide();
                    }
                    return;  // stop proceed with editable worklog setup
                }
                
                // STEP 2: Load worklog data (tasks, allocations)
                //  - Only load checkout data if worklog is editable (new worklogs or today's worklogs with open session)
                if (!context.is_read_only) {
                    load_worklog_data(frm).then(data => {
                        if (!data) return;
                        
                        // Merge context into worklog_data
                        frm.worklog_data = data;
                        frm.current_total = data[FIELD.TIME_TOTAL_ACTUAL];
                        frm.time_since_last_save = data[FIELD.TIME_SINCE_SAVE];

                        update_overview_headline(frm, data?.[FIELD.WORKLOG_HEADLINE], data.headline_color)

                        // check if this is an existing worklog (has saved tasks)
                        const hasExistingTasks = data[FIELD.EXISTING_TASKS] && data[FIELD.EXISTING_TASKS].length > 0;
                        
                        // Load tasks into form
                        if (hasExistingTasks) {
                            // a. Load existing saved tasks
                            load_tasks_into_form(frm, data[FIELD.EXISTING_TASKS], true);
                        }else if ((!frm.doc[FIELD.TASKS_ENTRY] || frm.doc[FIELD.TASKS_ENTRY].length === 0) && 
                            data[FIELD.PREFILLED_TASKS] && data[FIELD.PREFILLED_TASKS].length > 0) {
                            // b. Load prefilled tasks only for truly new worklogs
                            load_tasks_into_form(frm, data[FIELD.PREFILLED_TASKS], false);
                        }
                        
                        // Setup editable worklog UI
                        setup_editable_worklog_ui(frm);
                        
                        // Focus on empty fields
                        if (!frm.read_only) {
                            setTimeout(() => {
                                let isFieldFocused = WorklogHelpers.focusOnAnEmptyField(frm);
                                if (!isFieldFocused) {
                                    const workDesc = frm.fields_dict[FIELD.WORK_DESC];
                                    if (workDesc) WorklogHelpers.focusOnField(workDesc);
                                }
                            }, SHORT_INTERVAL_MS);
                        }
                    });
                } else if (frm.doc[FIELD.TASKS_ENTRY] && frm.doc[FIELD.TASKS_ENTRY].length > 0) {
                    // For read-only worklogs (historical/completed), just show allocation status if tasks exist
                    recalculate_allocation_status(frm);
                }
            }
        });

        // Set query for task field in tasks_entry child table
        frm.set_query(FIELD.TASK, FIELD.TASKS_ENTRY, function(doc, cdt, cdn) {
            const row = locals[cdt][cdn];
            
            // Get all currently selected tasks from the table
            const existing_tasks = (doc[FIELD.TASKS_ENTRY] || [])
                .map(r => r[FIELD.TASK])
                .filter(t => t && t !== row[FIELD.TASK]); // Exclude current row
            
            // Get buffer task ID
            const buffer_task_id = window.BUFFER_TASK_ID || '';
            
            return {
                filters: {
                    name: ["not in", [...existing_tasks, buffer_task_id]],
                    status: ["!=", "Cancelled"]
                }
            };
        });
    },

    /** 
     * Validate the Worklog document's required fields and display user-friendly warnings
     * Prevents submission if critical fields are missing/invalid
     */
    validate: function(frm) {
        // Don't allow saving historical/completed worklogs
        if (frm.read_only) {
            FrappeUtils.error_modal(MESSAGES.WARN_NO_MODIFY_WORKLOG, MESSAGES.NO_EDIT);
            frappe.validated = false;
            return false;
        }
    }
});

// ============ CHILD TABLE EVENTS ============
frappe.ui.form.on(DOCTYPE.CHILD, {
    [FIELD.TIME_SPENT]: function(frm, cdt, cdn) {        
        const row = locals[cdt][cdn];
        
        // Calculate progress increment
        if (row[FIELD.TIME_SPENT] && row[FIELD.EXPECTED_TIME] && row[FIELD.EXPECTED_TIME] > 0) {
            const increment = (row[FIELD.TIME_SPENT] / row[FIELD.EXPECTED_TIME]) * 100;            
            frappe.model.set_value(cdt, cdn, FIELD.PROGRESS_INCREMENT, Math.min(increment, 100));
        } else {
            frappe.model.set_value(cdt, cdn, FIELD.PROGRESS_INCREMENT, 0);
        }

        // Update allocation status indicator immediately
        recalculate_allocation_status(frm);
    },

    tasks_entry_remove: function(frm) {
        // Update allocation status when rows are removed
        recalculate_allocation_status(frm);
    }
});

// _________________________________________

async function load_worklog_data(frm) {
    // 1. Ensure we have employee ID first
    let employee_id = frm.doc.employee;
    // debugger
    if (!employee_id) {
        try {
            const employee = await FlextimeApi.fetchCurrentEmployee();
            employee_id = employee?.id;
            if (employee_id) {
                frm.set_value('employee', employee_id);
                WorklogHelpers.setEmployeeNameHint(frm, employee?.full_name);
            } else {
                // fetchCurrentEmployee succeeded but returned no ID
                FrappeUtils.error_modal(MESSAGES.ERR_NO_EMPLOYEE || MESSAGES.ERR_UNKNOWN);
                return null;
            }
        } catch (error) {
            console.error('Failed to get employee:', error);
            frappe.set_route('app/flextime')
            FrappeUtils.error_modal(error.message);
            FrappeUtils.toast_info(MESSAGES.REDIRECT_HOME);
            return null;
        }
    }

    // 2. Load worklog data
    try {
        const response = await frappe.call({
            method: API.WORKLOG.PREPARE_CHECKOUT,
            args: { employee_id: employee_id }
        });

        // Checking if response exists
        if (!response || !response.message) {
            FrappeUtils.error_modal(MESSAGES.ERR_NO_DATA_RECEIVED);
            return null;
        }

        const data = response.message;

        // Validate work time exists (defensive check - backend should handle this)
        if (!data.existing_worklog_name &&
            !data[FIELD.HAS_OPEN_SESSION] &&
            data[FIELD.TIME_TOTAL_ACTUAL] <= 0 &&
            (!data[FIELD.TIME_SAVED] || data[FIELD.TIME_SAVED] <= 0)) {
            FrappeUtils.error_modal(MESSAGES.ERR_NO_WORK_TIME, MESSAGES.TITLE_NO_WORK_TIME);
            frappe.set_route('app/flextime');
            return null;
        }

        // Store all data on frm (in-memory)
        frm.worklog_data = data;
        frm.current_total = data[FIELD.TIME_TOTAL_ACTUAL];    
        frm.time_since_last_save = data[FIELD.TIME_SINCE_SAVE];
        
        // Set form values
        frm.set_value(FIELD.TIME_SAVED, data[FIELD.TIME_SAVED]);
        
        // Set log_time for new forms
        if (frm.is_new() && !frm.doc[FIELD.LOG_TIME]) {
            frm.set_value(FIELD.LOG_TIME, FrappeUtils.get_db_format_time(new Date()));
        }
        
        return data;
    } catch (error) {
        // Network or transport error
        console.error('API call failed:', error);
        FrappeUtils.error_modal(
            error.message || MESSAGES.ERR_BACKEND_UNREACHABLE,
            MESSAGES.TITLE_ERROR
        );
        return null;
    }
}

function load_tasks_into_form(frm, tasks, isExisting = false) {
    if (!tasks || tasks.length === 0) return;
    
    // Clear existing rows
    frm.clear_table(FIELD.TASKS_ENTRY);
    
    // Add each task using add_child
    tasks.forEach(task => {
        let child = frm.add_child(FIELD.TASKS_ENTRY);
        child[FIELD.TASK] = task[FIELD.TASK];
        child[FIELD.SUBJECT] = task[FIELD.SUBJECT];
        child[FIELD.STATUS] = isExisting ? __(task[FIELD.STATUS]) : __(task[FIELD.STATUS] || '');
        child[FIELD.PRIORITY] = isExisting ? __(task[FIELD.PRIORITY]) : __(task[FIELD.PRIORITY] || '');
        child[FIELD.EXPECTED_TIME] = task[FIELD.EXPECTED_TIME] || 0;
        child[FIELD.TIME_SPENT] = isExisting ? (task[FIELD.TIME_SPENT] || 0) : 0;
        child[FIELD.TASK_DESC] = isExisting ? (task[FIELD.TASK_DESC] || '') : '';
        child.progress_increment = isExisting ? (task.progress_increment || 0) : 0;
    });
    
    // CRITICAL: This triggers the grid to re-render with the new data
    frm.refresh_field(FIELD.TASKS_ENTRY);
    
    // Additional grid refresh to ensure visibility
    const grid = frm.fields_dict[FIELD.TASKS_ENTRY]?.grid;
    if (grid) {
        grid.refresh();
    }
}

function recalculate_allocation_status(frm) {
    // For read-only worklogs, clear and hide the container
    if (frm.read_only || frm.worklog_context?.is_read_only) {
        const $container = frm.$wrapper.find('.allocation-mismatch-indicator');
        if ($container.length) {
            $container.empty();
            $container.hide();
        }
        return;
    }

    // Calculate current totals from the form
    let totalAllocated = 0;
    (frm.doc[FIELD.TASKS_ENTRY] || []).forEach(row => {
        if (row && row[FIELD.TIME_SPENT]) {
            totalAllocated += parseFloat(row[FIELD.TIME_SPENT]);
        }
    });

    const currentTotal = frm.current_total || frm.doc[FIELD.TIME_SAVED] || 0;
    const unallocated = currentTotal - totalAllocated;
    const tolerance = (frm.tolerance_minutes || DEFAULT_TOLERANCE_MINUTES) / 60;
    const absUnallocated = Math.abs(unallocated);

    // Determine status and message
    let statusClass = '';
    let messageHtml = '';

    if (absUnallocated <= 0.01) {
        statusClass = 'perfect';
        messageHtml = `<strong>${__("Perfectly allocated!")}</strong> ✅`;
    } else if (absUnallocated <= tolerance) {
        statusClass = 'warning';
        if (unallocated > 0) {
            messageHtml = `<span class="text-warning">▼</span> <strong>${unallocated.toFixed(2)} ${__("hrs")}</strong> ${__("left to allocate")} <span class="text-muted">(${__("within tolerance")} ✓)</span>`;
        } else {
            messageHtml = `<span class="text-warning">▲</span> <strong>${absUnallocated.toFixed(2)} ${__("hrs")}</strong> ${__("overallocated")} <span class="text-muted">(${__("within tolerance")} ✓)</span>`;
        }
    } else {
        statusClass = 'danger';
        if (unallocated > 0) {
            messageHtml = `<span class="text-danger">▼</span> <strong>${unallocated.toFixed(2)} ${__("hrs")}</strong> ${__("left to allocate")} <span class="text-danger">(${__("exceeds tolerance")} !)</span>`;
        } else {
            messageHtml = `<span class="text-danger">▲</span> <strong>${absUnallocated.toFixed(2)} ${__("hrs")}</strong> ${__("overallocated")} <span class="text-danger">(${__("exceeds tolerance")} !)</span>`;
        }
    }

    // Build HTML with CSS classes
    const html = `<div class="allocation-mismatch-indicator allocation-mismatch-${statusClass}"><div class="allocation-mismatch-content">${messageHtml}</div></div>`;
    
    // Find or create container below tasks table
    let $container = frm.$wrapper.find('.allocation-mismatch-below-table');
    
    if ($container.length === 0) {
        const $tableField = frm.fields_dict[FIELD.TASKS_ENTRY]?.$wrapper;
        if ($tableField) {
            $container = $('<div class="allocation-mismatch-below-table"></div>');
            $tableField.after($container);
        }
    }
    
    if ($container.length) {
        $container.html(html);
    }
}

function update_overview_headline(frm, template, color){
    setTimeout(() => {
        frm.dashboard.clear_headline();
        frm.dashboard.set_headline(template, color || 'red');
    }, SHORT_INTERVAL_MS);
}

function setup_editable_worklog_ui(frm) {
    const data = frm.worklog_data;
    const context = frm.worklog_context;

    if (!data || !context) return;

    const hasOpenSession = data[FIELD.HAS_OPEN_SESSION] || context[FIELD.HAS_OPEN_SESSION];
    
    // Handle Save & Checkout button
    frm.remove_custom_button(LBL_BTN_SAVE_AND_CHECKOUT);
    
    if (hasOpenSession) {
        frm.add_custom_button(LBL_BTN_SAVE_AND_CHECKOUT, () => {
            save_and_checkout_action(frm);
        });
    }
        
    // Always start refresh if not already running (don't stop on break)
    if (!frm.work_duration_recalculation_interval) {
        start_work_duration_refresh(frm);
    }

    // Show allocation status below tasks table
    recalculate_allocation_status(frm);
}

function set_form_read_only(frm, read_only) {

    if (read_only) {
        // Just add/remove a CSS class for visual styling
        frm.$wrapper.find('.form-section').addClass('historical-worklog');
        frm.disable_save();
        frm.disable_form()
    } else {
        frm.enable_save();
        frm.dashboard.clear_headline();
        frm.$wrapper.find('.form-section').removeClass('historical-worklog');
    }
}

function save_and_checkout_action(frm) {
    // Ensure current_total is a valid number
    let current_total = frm.current_total;
    if (current_total === undefined || current_total === null || current_total === '') {
        current_total = frm.doc[FIELD.TIME_SAVED] || 0;
    }
    current_total = parseFloat(current_total);
    if (isNaN(current_total)) {
        current_total = 0;
    }

    frappe.confirm(
        __(MESSAGES.CONFIRM_SAVE_AND_CHECKOUT),
        function() {
            const worklogData = {
                [FIELD.WORK_DESC]: frm.doc[FIELD.WORK_DESC],
                [FIELD.IS_HOME_OFFICE]: frm.doc[FIELD.IS_HOME_OFFICE],
                [FIELD.TICKET_LINK]: frm.doc[FIELD.TICKET_LINK],
                [FIELD.TIME_SAVED]: frm.doc[FIELD.TIME_SAVED],
                [FIELD.TASKS_ENTRY]: (frm.doc[FIELD.TASKS_ENTRY] || []).map(row => ({
                    [FIELD.TASK]: row[FIELD.TASK],
                    [FIELD.SUBJECT]: row[FIELD.SUBJECT],
                    [FIELD.EXPECTED_TIME]: parseFloat(row[FIELD.EXPECTED_TIME]) || 0,
                    [FIELD.TIME_SPENT]: parseFloat(row[FIELD.TIME_SPENT]) || 0,
                    [FIELD.PROGRESS_INCREMENT]: parseFloat(row[FIELD.PROGRESS_INCREMENT]) || 0,
                    [FIELD.STATUS]: row[FIELD.STATUS],
                    [FIELD.TASK_DESC]: row[FIELD.TASK_DESC] || '',
                    [FIELD.PRIORITY]: row[FIELD.PRIORITY] || ''
                }))
            };

            frappe.call({
                method: API.WORKLOG.SAVE_AND_CHECKOUT,
                args: {
                    worklog_name: frm.is_new() ? null : frm.doc.name,
                    employee_id: frm.doc.employee,
                    worklog_data: worklogData,
                    current_total: frm.current_total,
                },
                callback: function(r) {
                    const res = r.message;

                    if (res && res.status === 'success') {
                        FrappeUtils.toast_success(res.message || 'success');

                        if (window.refreshCheckinOptions) {
                            window.refreshCheckinOptions();
                        }

                        frappe.set_route('desk');
                    } else if (res && res.status === 'error') {
                        FrappeUtils.toast_failure(res.message || 'failure');
                    }
                }
            });
        }
    );
}