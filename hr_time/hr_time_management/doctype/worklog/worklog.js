// Copyright (c) 2024, AtlasAero GmbH and contributors
// For license information, please see license.txt

const PREV_WFH_PREF_KEY = HR_TIME?.LS_KEYS?.PREV_WFH_PREF || 'neo_hr_time_last_wfh_value';
const WORK_DURATION_RECALC_INTERVAL = 10_000
let CACHED_TOLERANCE_MINUTES = null;
const LBL_BTN_SAVE_AND_CHECKOUT = 'Save & Checkout'

const WorklogHelpers = {
    /** Fetch and set HomeOffice value from the LocalStorage */
    restoreWfhPreference: function(frm) {
        // Only apply to new forms, not existing ones
        if (!frm.is_new()) return;

        const wfhPref = JsUtils.getStringFromLocalStore(PREV_WFH_PREF_KEY);
        if (wfhPref) {
            frm.set_value('is_home_office', wfhPref);
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

    setTasksAllocationHint: function(frm, allocationHint) {        
        const taskEntryField = frm.fields_dict.tasks_entry;
        if (!taskEntryField) return;
        
        const wrapper = taskEntryField.wrapper;
        const helpBox = wrapper.querySelector('p.help-box');
        
        if (helpBox) {            
            helpBox.textContent = allocationHint;
        }
    },

    /**
     * Focuses on the first empty field based on fixed priority.
     * @returns {boolean} - whether a field was focused
     */
    focusOnAnEmptyField: function(frm){
        const fieldPriority = [  // Field focus priority (which aren't auto filled)
                'task_desc',
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

    /** Format duration for display */
    formatDuration: function(hours) {
        const h = Math.floor(hours);
        const m = Math.round((hours - h) * 60);
        return `${h}h ${m}m`;
    },
};

// Add this helper function at the top level (after WorklogHelpers)
function validate_worklog_for_checkout(frm) {
    // 1. Check if there's any work time recorded
    const currentTotal = frm.current_total || frm.doc.time_saved;
    if (!currentTotal || currentTotal <= 0) {
        FrappeUtils.error_modal(MESSAGES.ERR_NO_WORK_TIME, MESSAGES.TITLE_NO_WORK_TIME);
        return false;
    }
    
    // 2. Check if any tasks have time allocated
    const hasAllocations = (frm.doc.tasks_entry || []).some(row => 
        row.time_spent && parseFloat(row.time_spent) > 0
    );
    
    if (!hasAllocations) {
        FrappeUtils.warn_user(MESSAGES.ERR_NO_TASK_ALLOCATIONS, MESSAGES.TITLE_NO_TASK_ALLOCATIONS);
        return false;
    }
    
    // 3. Check basic required fields
    if (!frm.doc.employee) {
        FrappeUtils.error_modal(MESSAGES.ERR_MISSING_EMPLOYEE, MESSAGES.TITLE_MISSING_EMPLOYEE)
        return false;
    }
    
    if (!frm.doc.is_home_office) {
        FrappeUtils.warn_user(MESSAGES.ERR_MISSING_HOME_OFFICE, MESSAGES.TITLE_MISSING_HOME_OFFICE);
        return false;
    }
    
    // 4. Check time allocation (same logic as backend, but frontend)
    let totalAllocated = 0;
    (frm.doc.tasks_entry || []).forEach(row => {
        if (row && row.time_spent) {
            totalAllocated += parseFloat(row.time_spent);
        }
    });
    
    const unallocated = currentTotal - totalAllocated;
    const tolerance = (frm.tolerance_minutes || 30) / 60;
    const absDifference = Math.abs(unallocated);
    
    // 5. Check time allocation within tolerance
    if (absDifference > tolerance) {
        if (unallocated > 0) {
            const msg = MESSAGES.ERR_UNDER_ALLOCATED
                .replace('{0}', unallocated.toFixed(2))
                .replace('{1}', tolerance.toFixed(2));
                FrappeUtils.error_modal(msg, MESSAGES.TITLE_UNDER_ALLOCATED);        }
        else {
            const msg = MESSAGES.ERR_OVER_ALLOCATED
                .replace('{0}', Math.abs(unallocated).toFixed(2))
                .replace('{1}', tolerance.toFixed(2));
                FrappeUtils.error_modal(msg, MESSAGES.TITLE_OVER_ALLOCATED);        }
        return false;
    }
    
    return true;
}

function get_tolerance_minutes(frm, callback) {
    if (CACHED_TOLERANCE_MINUTES !== null) {
        frm.tolerance_minutes = CACHED_TOLERANCE_MINUTES;
        if (callback) callback(CACHED_TOLERANCE_MINUTES);
        return;
    }
    
    frappe.call({
        method: "hr_time.api.worklog.api.get_tolerance_minutes",
        callback: function(r) {
            CACHED_TOLERANCE_MINUTES = r.message || 30;
            frm.tolerance_minutes = CACHED_TOLERANCE_MINUTES;
            if (callback) callback(CACHED_TOLERANCE_MINUTES);
        }
    });
}

// Start auto-refresh when form opens
// let frm.work_duration_recalculation_interval = null;

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

    // Refresh every 15 seconds
    frm.work_duration_recalculation_interval = setInterval(() => {
        const isFullForm = frappe.get_route()[0] === 'Form' && frappe.get_route()[1] === 'Worklog'

        if(!isFullForm){
            stop_work_duration_refresh(frm)
            return
        }

        if (frm.doc.employee) {
            refresh_work_duration(frm);
        }
    }, WORK_DURATION_RECALC_INTERVAL);
}

// Helper to refresh work duration
function refresh_work_duration(frm) {
    frappe.call({
        method: "hr_time.api.worklog.api.prepare_worklog_for_checkout",
        args: { employee_id: frm.doc.employee },
        callback: function(r) {
            const data = r.message
            if (data) {
                // Update stored data on frm
                frm.worklog_data = data;
                frm.current_total = data.time_total_actual;
                frm.time_since_last_save = data.time_since_last_save;
                frm.set_value('time_saved', data.time_saved);

                if (data.worklog_overview_headline) {
                    update_overview_headline(frm, data.worklog_overview_headline, data.headline_color)
                }

                // Update allocation status below table
                recalculate_allocation_status(frm)

                // ✅ Update Save & Checkout button based on current state
                frm.remove_custom_button(__(LBL_BTN_SAVE_AND_CHECKOUT));
                if (data.has_open_session && !frm.read_only) {
                    frm.add_custom_button(__(LBL_BTN_SAVE_AND_CHECKOUT), () => {
                        if (validate_worklog_for_checkout(frm)) {
                            save_and_checkout_action(frm);
                        }
                    });
                }
            }
        }
    });
}

frappe.ui.form.on('Worklog', {

    onload: function(frm) {
        WorklogHelpers.localizePlaceholders(frm);
        WorklogHelpers.restoreWfhPreference(frm);

        // Fetch tolerance once
        get_tolerance_minutes(frm);
    },

    /** Update 'Home Office' preference in localStorage before saving worklog */
    before_save: function(frm) {
        // Before saving, set a custom property on the document
        // that will be sent to the server
        if (frm.current_total) {
            frm.doc.__current_total = frm.current_total;
        }        
        
        if (['Yes', 'No'].includes(frm.doc.is_home_office)){
            JsUtils.saveStringToLocalStore(PREV_WFH_PREF_KEY, frm.doc.is_home_office);
        }
    },

    refresh: function(frm) {
        // CRITICAL: Reset ALL cached data when form loads
        frm.worklog_data = null;
        frm.worklog_context = null;
        frm.current_total = null;
        frm.time_since_last_save = null;
        frm.tolerance_minutes = null;

        // Set log_time for new forms
        if (frm.is_new() && !frm.doc.log_time) {
            frm.set_value('log_time', FrappeUtils.get_db_format_time(new Date()));
        }

        // Clear any stale tasks for new forms
        if (frm.is_new() && frm.doc.tasks_entry && frm.doc.tasks_entry.length > 0) {
            frm.clear_table('tasks_entry');
            frm.refresh_field('tasks_entry');
        }

        // ============================================
        // STEP 1: Get worklog context (unified for all worklogs)
        // ============================================
        frappe.call({
            method: "hr_time.api.worklog.api.get_worklog_context",
            args: {
                worklog_name: frm.is_new() ? null : frm.doc.name,
                employee_id: frm.doc.employee
            },
            callback: function(r) {
                if (!r.message) return;
                
                const context = r.message;

                // REDIRECT: If this is a new form but there's already a worklog for today
                if (frm.is_new() && context.today_worklog_name && context.today_worklog_name !== frm.doc.name) {
                    FrappeUtils.alert_info(MESSAGES.INFO_OPENING_EXISTING, 3);
                    frappe.set_route('Form', 'Worklog', context.today_worklog_name);
                    return;
                }

                frm.worklog_context = context;
                frm.tolerance_minutes = context.tolerance_minutes;
                
                // Set dashboard headline using pre-rendered HTML
                if (context.worklog_overview_headline) {
                    update_overview_headline(frm, context.worklog_overview_headline)
                }
                
                // Set read-only state based on backend
                set_form_read_only(frm, context.is_read_only);

                // For read-only worklogs (historical/completed)
                if (context.is_read_only) {
                    const $container = frm.$wrapper.find('.allocation-mismatch-indicator');
                    if ($container.length) {
                        $container.empty();
                        $container.hide();
                    }
                    return;
                }
                
                // ============================================
                // STEP 2: Load worklog data (tasks, allocations)
                // ============================================
                // Only load checkout data if worklog is editable
                // (new worklogs or today's worklogs with open session)
                if (!context.is_read_only) {
                    load_worklog_data(frm).then(data => {
                        if (!data) return;
                        
                        // Merge context into worklog_data
                        frm.worklog_data = data;
                        frm.current_total = data.time_total_actual;
                        frm.time_since_last_save = data.time_since_last_save;

                        update_overview_headline(frm, data?.worklog_overview_headline, data.headline_color)

                        // check if this is an existing worklog (has saved tasks)
                        const hasExistingTasks = data.existing_tasks && data.existing_tasks.length > 0;
                        
                        // Load tasks into form
                        if (hasExistingTasks) {
                            // Load existing saved tasks
                            load_tasks_into_form(frm, data.existing_tasks, true);
                        }else if ((!frm.doc.tasks_entry || frm.doc.tasks_entry.length === 0) && 
                            data.prefilled_tasks && data.prefilled_tasks.length > 0) {
                            // Load prefilled tasks only for truly new worklogs
                            load_tasks_into_form(frm, data.prefilled_tasks, false);
                        }
                        
                        // Setup editable worklog UI
                        setup_editable_worklog_ui(frm);
                        
                        // Focus on empty fields
                        if (!frm.read_only) {
                            setTimeout(() => {
                                let isFieldFocused = WorklogHelpers.focusOnAnEmptyField(frm);
                                if (!isFieldFocused) {
                                    const taskDesc = frm.fields_dict['task_desc'];
                                    if (taskDesc) WorklogHelpers.focusOnField(taskDesc);
                                }
                            }, 100);
                        }
                    });
                } else if (frm.doc.tasks_entry && frm.doc.tasks_entry.length > 0) {
                    // For read-only worklogs (historical/completed), just show allocation status if tasks exist
                    recalculate_allocation_status(frm);
                }
            }
        });

        // ✅ Set query for task field in tasks_entry child table
        frm.set_query('task', 'tasks_entry', function(doc, cdt, cdn) {
            const row = locals[cdt][cdn];
            
            // Get all currently selected tasks from the table
            const existing_tasks = (doc.tasks_entry || [])
                .map(r => r.task)
                .filter(t => t && t !== row.task); // Exclude current row
            
            // Get buffer task ID (you need to fetch or store it)
            // Option 1: Fetch from cache or global
            const buffer_task_id = window.BUFFER_TASK_ID || '';
            
            // Option 2: Fetch via API (but that's async, so better to cache)
            
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
            frappe.msgprint({
                title: __('Cannot Edit'),
                message: __('This worklog is historical and cannot be modified.'),
                indicator: 'red'
            });
            frappe.validated = false;
            return false;
        }

        // Reuse the same validation logic
        if (!validate_worklog_for_checkout(frm)) {
            frappe.validated = false;
            return false;
        }
    }
});

// ============ CHILD TABLE EVENTS ============
frappe.ui.form.on('Worklog Tasks', {
    time_spent: function(frm, cdt, cdn) {        
        const row = locals[cdt][cdn];
        
        // Calculate progress increment
        if (row.time_spent && row.expected_time && row.expected_time > 0) {
            const increment = (row.time_spent / row.expected_time) * 100;            
            frappe.model.set_value(cdt, cdn, "progress_increment", Math.min(increment, 100));
        } else {
            frappe.model.set_value(cdt, cdn, "progress_increment", 0);
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
    // Ensure we have employee ID first
    let employee_id = frm.doc.employee;

    if (!employee_id) {
        try {
            const employee = await FlextimeApi.fetchCurrentEmployee();
            employee_id = employee?.id;
            if (employee_id) {
                frm.set_value('employee', employee_id);
                WorklogHelpers.setEmployeeNameHint(frm, employee?.full_name);
            }
        } catch (error) {
            console.error('Failed to get employee:', error);
            frappe.msgprint(__('Could not identify current employee'));
            return null;
        }
    }

    if (!employee_id) {
        frappe.msgprint(__('Employee not found'));
        return null;
    }

    // Load worklog data
    const response = await frappe.call({
        method: "hr_time.api.worklog.api.prepare_worklog_for_checkout",
        args: { employee_id: employee_id }
    });

    if (!response.message) return null;

    const data = response.message;

    if (!data.existing_worklog_name && !data.has_open_session && data.time_total_actual<=0 && (!data.time_saved || data.time_saved <= 0)) {
        FrappeUtils.error_modal(MESSAGES.ERR_NO_WORK_TIME, MESSAGES.TITLE_NO_WORK_TIME);
        frappe.set_route('app/flextime');
        return null;
    }

    // Store all data on frm (in-memory)
    frm.worklog_data = data;
    frm.current_total = data.time_total_actual;    
    frm.time_since_last_save = data.time_since_last_save;
    
    // Set form values
    frm.set_value('time_saved', data.time_saved);
    
    // Set log_time for new forms
    if (frm.is_new() && !frm.doc.log_time) {
        frm.set_value('log_time', FrappeUtils.get_db_format_time(new Date()));
    }
    
    return data;
}

function load_tasks_into_form(frm, tasks, isExisting = false) {
    if (!tasks || tasks.length === 0) return;
    
    // Clear existing rows
    frm.clear_table('tasks_entry');
    
    // Add each task using add_child
    tasks.forEach(task => {
        let child = frm.add_child('tasks_entry');
        child.task = task.task;
        child.task_subject = task.task_subject;
        child.task_status = task.task_status || 'Open';
        child.priority = task.priority || '';
        child.expected_time = task.expected_time || 0;
        child.time_spent = isExisting ? (task.time_spent || 0) : 0;
        child.description = isExisting ? (task.description || '') : '';
        child.progress_increment = isExisting ? (task.progress_increment || 0) : 0;
    });
    
    // CRITICAL: This triggers the grid to re-render with the new data
    frm.refresh_field('tasks_entry');
    
    // Additional grid refresh to ensure visibility
    const grid = frm.fields_dict.tasks_entry?.grid;
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
    (frm.doc.tasks_entry || []).forEach(row => {
        if (row && row.time_spent) {
            totalAllocated += parseFloat(row.time_spent);
        }
    });
    
    const currentTotal = frm.current_total || frm.doc.time_saved || 0;
    const unallocated = currentTotal - totalAllocated;
    const tolerance = (frm.tolerance_minutes || 30) / 60;
    const absUnallocated = Math.abs(unallocated);
    
    // Determine status and message
    let statusClass = '';
    let messageHtml = '';
    
    if (absUnallocated <= 0.01) {
        statusClass = 'perfect';
        messageHtml = '✅ <strong>Perfectly allocated!</strong>';
    } else if (absUnallocated <= tolerance) {
        statusClass = 'warning';
        if (unallocated > 0) {
            messageHtml = `⚠️ <strong>${unallocated.toFixed(2)} hrs left to allocate</strong> <span class="text-muted">(within tolerance ✓)</span>`;
        } else {
            messageHtml = `⚠️ <strong>${absUnallocated.toFixed(2)} hrs overallocated</strong> <span class="text-muted">(within tolerance ✓)</span>`;
        }
    } else {
        statusClass = 'danger';
        if (unallocated > 0) {
            messageHtml = `❌ <strong>${unallocated.toFixed(2)} hrs left to allocate</strong> <span class="text-danger">(exceeds tolerance❗)</span>`;
        } else {
            messageHtml = `❌ <strong>${absUnallocated.toFixed(2)} hrs overallocated</strong> <span class="text-danger">(exceeds tolerance❗)</span>`;
        }
    }
    
    // Build HTML with CSS classes
    const html = `<div class="allocation-mismatch-indicator allocation-mismatch-${statusClass}"><div class="allocation-mismatch-content">${messageHtml}</div></div>`;
    
    // Find or create container below tasks table
    let $container = frm.$wrapper.find('.allocation-mismatch-below-table');
    
    if ($container.length === 0) {
        const $tableField = frm.fields_dict.tasks_entry?.$wrapper;
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
        frm.dashboard.set_headline(template, color || 'gray');
    }, 100);
}

function setup_editable_worklog_ui(frm) {
    const data = frm.worklog_data;
    const context = frm.worklog_context;
    
    if (!data || !context) return;
    
    // const isEditable = !context.is_read_only;
    const hasOpenSession = data.has_open_session || context.has_open_session;
    
    // Handle Save & Checkout button
    frm.remove_custom_button(__(LBL_BTN_SAVE_AND_CHECKOUT));
    
    if (hasOpenSession) { //isEditable && hasOpenSession
        frm.add_custom_button(__(LBL_BTN_SAVE_AND_CHECKOUT), () => {
            if (validate_worklog_for_checkout(frm)) {
                save_and_checkout_action(frm);
            }
        });
    }
        
    // ✅ Always start refresh if not already running (don't stop on break)
    if (!frm.work_duration_recalculation_interval) {
        start_work_duration_refresh(frm);
    }

    // Show allocation status below tasks table
    recalculate_allocation_status(frm);
}

function get_current_state(frm, data) {
    // If data is not provided, try to use worklog_data or worklog_context
    if (!data) {
        data = frm.worklog_data || frm.worklog_context;
    }
    if (!data) return 'historical';

    const isTodaysWorklog = data.existing_worklog_name || frm.worklog_context?.is_todays_worklog;

    if (frm.is_new() && !data.existing_worklog_name) {
        return 'new';
    } else if (isTodaysWorklog) {
        if (data.has_open_session) return 'working';
        if (data.on_break) return 'break';
        return 'completed';
    }
    return 'historical';
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

function get_worklog_state(data, is_new, is_todays) {
    if (is_new && !data.existing_worklog_name) return 'new';
    if (!is_todays) return 'historical';
    if (data.has_open_session) return 'working';
    if (data.on_break) return 'break';
    return 'completed';
}

function save_and_checkout_action(frm) {
    // Ensure current_total is a valid number
    let current_total = frm.current_total;
    if (current_total === undefined || current_total === null || current_total === '') {
        current_total = frm.doc.time_saved || 0;
    }
    current_total = parseFloat(current_total);
    if (isNaN(current_total)) {
        current_total = 0;
    }

    frappe.confirm(
        __(MESSAGES.CONFIRM_SAVE_AND_CHECKOUT),
        function() {
            const worklogData = {
                task_desc: frm.doc.task_desc,
                is_home_office: frm.doc.is_home_office,
                ticket_link: frm.doc.ticket_link,
                time_saved: frm.doc.time_saved,
                tasks_entry: (frm.doc.tasks_entry || []).map(row => ({
                    task: row.task,
                    task_subject: row.task_subject,
                    expected_time: parseFloat(row.expected_time) || 0,
                    time_spent: parseFloat(row.time_spent) || 0,
                    progress_increment: parseFloat(row.progress_increment) || 0,
                    task_status: row.task_status,
                    description: row.description || '',
                    priority: row.priority || ''
                }))
            };

            frappe.call({
                method: "hr_time.api.worklog.api.save_and_checkout",
                args: {
                    worklog_name: frm.is_new() ? null : frm.doc.name,
                    employee_id: frm.doc.employee,
                    worklog_data: worklogData,
                    current_total: frm.current_total,
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        FrappeUtils.alert_success(MESSAGES.SUCCESS_WORKLOG_SAVED);

                        if (window.refreshCheckinOptions) {
                            window.refreshCheckinOptions();
                        }

                        frappe.set_route('desk');
                    } else if (r.message && r.message.error) {
                        FrappeUtils.alert_failure(r.message.error);
                    }
                }
            });
        }
    );
}