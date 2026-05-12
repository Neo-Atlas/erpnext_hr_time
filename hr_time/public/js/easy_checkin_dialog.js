import { EasyCheckinStatus } from "./easy_checkin_status";
import { FrappeUtils } from "./utils/frappe_utils";


const DEFAULT_TOLERANCE_MINUTES = 0

const FIELD = {
    WORKLOG_STATUS_CONTAINER: "worklog_status_container",
    WORKLOG_BOX: "worklog_box",
    TIME_SAVED: "time_saved",
    TIME_SPENT: "time_spent",
    TIME_TOTAL_ACTUAL: "time_total_actual",
    TIME_SINCE_SAVE: "time_since_last_save",
    WORK_DURATION: "work_duration",
    TOLERANCE_MIN: "tolerance_minutes",
    EXISTING_TASKS: "existing_tasks",
    EXPECTED_TIME: "expected_time",
    TASK: "task",
    SUBJECT: "subject",
    PRIORITY: "priority",
    STATUS: "status",
    PROGRESS_INCREMENT: "progress_increment",
    TASK_DESC: "task_desc",
    PREFILLED_TASKS: "prefilled_tasks",
    TASKS_ENTRY: "tasks_entry",
    WORK_DESC: "work_desc",
    TICKET_LINK: "ticket_link",
    EXTERNAL_REFERENCE: "external_reference",
    IS_HOME_OFFICE: "is_home_office",
    WORKLOG_FULL_FORM_BTN: "worklog_full_form_btn",
    ALLOCATION_STATUS_CONTAINER: "allocation_status_container",
};

/** Predefined Action options for Checkin events */
const ACTIONS = {
  EOW: 'End of work',
  BRK: 'Break',
  RSM: 'Resume work',
  SOW: 'Start of work'
};

/** 
 * Fixed text definitions for various labels in the Dialog
 */
const LABELS = {
  TITLE: "Easy Checkin",
  PRIMARY_ACTION_BTN: "Submit"
}

const DOCTYPE = {
  NAME:'Worklog', 
  CHILD: 'Worklog Tasks'
}

/**
 * Class representing the EasyCheckinDialog for managing employee check-ins.
 */
export class EasyCheckinDialog {
  /**
   * Array of options available for check-in actions.
   * @type {Array<string>}
   */
  options = [];

  /**
   * Default check-in action.
   * @type {string}
   */
  default = "";

  /**
   * Reference to the Frappe's dialog UI instance.
   * @type {Object}
   */
  dialogUI;

  /**
   * Array of buttons to refresh the dashboard UI.
   * @type {Array<Element>}
   */
  refresh_buttons;


  /** The local Storage key to be used to save/get WFH preference. */
  static PREV_WFH_PREF_KEY = ''

  constructor() {    
    this.isDialogCurrentlyOpen = false;
    this.isRefreshing = false;
    this.refreshInterval = null;
    this.PREV_WFH_PREF_KEY = HR_TIME?.LS_KEYS?.PREV_WFH_PREF || 'neo_hr_time_last_wfh_value'
  }

  /** Preloads the current checkin status */
  async preloadCheckinOptions() {
    try {
      const response = await frappe.call({
        method: API.FLEXTIME.GET_OPTIONS,
      });
      this.options = response.message.options;
      this.default = response.message.default;
    } catch (error) {
      console.error(MESSAGES.FAILED_PRELOAD_CHECKIN_OPTIONS, error);
    }
  }

  /** Initiates Checkin dialog creation after fetching current employee's ID. */
  async show() {
    try{
      const employee_id = await FlextimeApi.fetchCurrentEmployeeId()
      this.createCheckinDialog(employee_id);
    } catch (error) {
      FrappeUtils.error_modal(error.message || MESSAGES.ERR_UNKNOWN);
    }
  }

  /**
   * Creates and displays the check-in dialog with options and actions.
   * @param {string} employee_id - The ID of the employee to create Checkin actions for.
   */
  createCheckinDialog(employee_id) {
  
    const lastHomeOfficeValue = JsUtils.getStringFromLocalStore(this.PREV_WFH_PREF_KEY);
    
    this.dialogUI = new frappe.ui.Dialog({
      title: __(LABELS.TITLE),
      fields: this.getDialogFields(employee_id, lastHomeOfficeValue),
      size: "large",
      primary_action_label: __(LABELS.PRIMARY_ACTION_BTN, undefined, "checkin"),
      primary_action: (values) => {
        const actionValue = values.action;
        const isEndOfWork = actionValue === ACTIONS.EOW;    
        
        if (!isEndOfWork) {
          // Not End of Work then simply proceed with Checkin
          this.submitCheckin(values, employee_id);
          return;
        }
        
        // Case: End of Work - need to validate worklog
        const work_desc = this.dialogUI.get_value(FIELD.WORKLOG_BOX);
        const trimmed_worklog_text = work_desc ? work_desc.trim() : '';
        
        if (!trimmed_worklog_text) {
          // Work description is required for both new and existing worklogs
          const hasWorklogs = !!this.dialogUI.worklog_context?.today_worklog_name;
          const message = hasWorklogs ? MESSAGES.EMPTY_WORK_DESC_WHEN_WORKLOG_EXISTS : MESSAGES.EMPTY_WORK_DESC_WHEN_NO_WORKLOGS;
          FrappeUtils.warn_user(message);
          return; // Don't proceed with checkout
        }
          const ticket_link = this.dialogUI.get_value([FIELD.EXTERNAL_REFERENCE]).trim();
          const is_home_office = this.dialogUI.get_value([FIELD.IS_HOME_OFFICE]);
          this.submitCheckinAfterAddingWorklog(values, employee_id, trimmed_worklog_text, ticket_link,
            is_home_office);
      },
      onhide: () => {
        this.isDialogCurrentlyOpen = false;
        this.stopPeriodicRefresh();  // Stop periodic refresh when leaving End of Work
      }
    });

    this.dialogUI.$wrapper.addClass("easy-checkin-dialog");
    this.initializeDialog(employee_id);
  }

  /**
   * Returns the configuration of fields to be displayed in the check-in dialog.
   * @returns {Array<Object>} - The fields configuration for Frappe's UI dialog.
   * @param {string} employee_id - The ID of the employee
   * @param {boolean} lastHomeOfficeValue - Previous workday's work place.
   */
  getDialogFields(employee_id, lastHomeOfficeValue) {

    return [
      {
        label: "Action",
        fieldname: "action",
        fieldtype: "Select",
        options: this.options,
        default: this.default,
        change: () => this.updateDialogBasedOnAction(employee_id),
      },
      {
        fieldtype: "Section Break",
        depends_on: `eval: doc.action === '${ACTIONS.EOW}'`,
      },
      {
        fieldname: FIELD.WORKLOG_STATUS_CONTAINER,
        fieldtype: "HTML",
        label: "",
        depends_on: `eval: doc.action === '${ACTIONS.EOW}'`,
      },
      {
        fieldname: FIELD.WORKLOG_BOX,
        fieldtype: "Text",
        label: "Add Worklog",
        placeholder: __("Summarize your work for the day"),
        depends_on: `eval: doc.action === '${ACTIONS.EOW}'`,
      },
      {
        fieldname: FIELD.TASKS_ENTRY,
        fieldtype: "Table",
        label: __("Allocate hours to tasks"),
        options: DOCTYPE.CHILD,
        depends_on: `eval: doc.action === '${ACTIONS.EOW}'`,
        reqd: 0,
        fields: [
          {
            fieldname: FIELD.TASK,
            fieldtype: "Link",
            options: "Task",
            in_list_view: 1,
            label: "Ticket",
            reqd: 1,
            columns: 3,
            fetch_from: "task.subject",
            fetch_if_empty: true,
            get_query: () => {
              const table_field = this.dialogUI.fields_dict[FIELD.TASKS_ENTRY];
              const existing_tasks = (table_field?.df?.data || [])
                  .map(row => row[FIELD.TASK])
                  .filter(Boolean);

              const buffer_task_id = window.BUFFER_TASK_ID || '';
              const user_id = frappe.session.user;
              
              return {
                filters: {
                    name: ["not in", [...existing_tasks, buffer_task_id]],
                    status: ["not in", ["Cancelled","Completed"]],
                },
                query: "hr_time.api.task.api.task_query_with_assignment",  // Custom method
              };
            },
            onchange: function(e) {
              const grid_context = this;

              const row = this.doc;
              if (row[FIELD.TASK]) {
                  // Fetch task details
                  frappe.call({
                      method: API.CLIENT.GET_DOC,
                      args: {
                          doctype: "Task",
                          name: row[FIELD.TASK]
                      },
                      callback: function(r) {
                        const data = r.message || {}
                          if (data) {
                            row[FIELD.SUBJECT] = data[FIELD.SUBJECT]
                            row[FIELD.EXPECTED_TIME] = data[FIELD.EXPECTED_TIME] || 0
                            row[FIELD.PRIORITY] = data[FIELD.PRIORITY] || ""
                            row[FIELD.STATUS] =  data[FIELD.STATUS] || ""
                              
                            // Refresh the specific row in the grid
                            if (grid_context.grid_row) {
                              grid_context.grid_row.refresh();
                            }
                          }
                      }
                  });
              }
          }
          },
          {
            fieldname: FIELD.SUBJECT,
            fieldtype: "Data",
            label: __("Ticket Name"),
            read_only: 1,
            in_list_view: 1,
            columns: 5,
          },
          {
            fieldname: FIELD.EXPECTED_TIME,
            fieldtype: "Float",
            label: __("Est. Time (hrs)"),
            read_only: 1,
            in_list_view: 0,
            columns: 1,
            precision: 2,
            fetch_from: `task${[FIELD.EXPECTED_TIME]}`
          },
          {
            fieldname: FIELD.TIME_SPENT,
            fieldtype: "Float",
            label: __("Time Spent (hrs)"),
            in_list_view: 1,
            columns: 2,
            reqd: 1,
            precision: 2,
            onchange: function () {
              const row = this.doc;
              if (!row[FIELD.EXPECTED_TIME] || row[FIELD.EXPECTED_TIME] === 0) return;

              const value = (row[FIELD.TIME_SPENT] / row[FIELD.EXPECTED_TIME]) * 100;
              row[FIELD.PROGRESS_INCREMENT] = value

              // Refresh depending on context
              if(this.grid){
                // Grid inline edit
                this.grid.refresh();
              }else if (this.layout?.refresh) {
                // Edit row dialog form
                this.layout.refresh();
              }

              // Update the allocation status display
              const dialog = window.easy_checkin_dialog;
              if (dialog && dialog.refresh_allocation_status_frontend) {
                dialog.refresh_allocation_status_frontend()
              }
            }
          },
          {
            fieldname: FIELD.STATUS,
            fieldtype: "Data",
            label: __("Status"),
            read_only: 1,
            in_list_view: 0,
            columns: 1,
            fetch_from: "task.status"
          },
          {
            fieldname: FIELD.PRIORITY,
            fieldtype: "Data",
            label: __("Priority"),
            read_only: 1,
            in_list_view: 0,
            columns: 1,
            fetch_from: `task.priority`
          },
          {
            fieldname: FIELD.PROGRESS_INCREMENT,
            fieldtype: "Percent",
            label: __("Progress Added (%)"),
            read_only: 1,
            in_list_view: 0,
            columns: 2,
            precision: 1
          }
        ],
        data: [], // Will be populated dynamically
        get_data: () => {
            // Always return an array
            const tasks = this.dialogUI?.worklog_data?.[FIELD.EXISTING_TASKS] || 
                          this.dialogUI?.worklog_data?.[FIELD.PREFILLED_TASKS] || [];
            return Array.isArray(tasks) ? tasks : [];
        }
      },
      {
        fieldname: FIELD.ALLOCATION_STATUS_CONTAINER,
        fieldtype: "HTML",
        depends_on: `eval: doc.action === '${ACTIONS.EOW}'`,
      },
      {
        label: __("External reference ↗"),
        fieldname: FIELD.EXTERNAL_REFERENCE,
        fieldtype: "Data",
        options: "URL", // Validate as a URL
        placeholder: __("e.g. link to a ticket in an external system"),
        depends_on: `eval: doc.action === '${ACTIONS.EOW}'`,
        reqd: false,
      },
      {
        label: "Home Office",
        fieldname: FIELD.IS_HOME_OFFICE,
        fieldtype: "Select",
        default: lastHomeOfficeValue,
        depends_on: `eval: doc.action === '${ACTIONS.EOW}'`,
        placeholder: __("Yes/No"),
        options: "\nYes\nNo",
      },
      {
        fieldname: FIELD.WORKLOG_FULL_FORM_BTN,
        fieldtype: "Button",
        label: __("Enter complete detail ↗"),
        depends_on: `eval: doc.action === '${ACTIONS.EOW}'`,
        click: () => {
            const existingWorklogName = this.dialogUI.worklog_data?.existing_worklog_name;

            // Get all dialog values
            const taskDesc = this.dialogUI.get_value(FIELD.WORKLOG_BOX) || '';
            const ticket_link = this.dialogUI.get_value([FIELD.EXTERNAL_REFERENCE])?.trim() || '';
            const is_home_office = this.dialogUI.get_value([FIELD.IS_HOME_OFFICE]) || '';
            
            if(is_home_office){
              JsUtils.saveStringToLocalStore(this.PREV_WFH_PREF_KEY, is_home_office);
            }

            if (existingWorklogName) {
                // Open existing worklog
                frappe.set_route(
                  'Form',
                  DOCTYPE.NAME,//'Worklog',
                  existingWorklogName
                );
            }else{
              frappe.new_doc(DOCTYPE.NAME, {
                  [FIELD.WORK_DESC]: taskDesc,
                  [FIELD.TICKET_LINK]: ticket_link,
                  [FIELD.IS_HOME_OFFICE]: is_home_office,
              });
            }
        },
      }
    ];
  }

  /**
   * Updates the dialog UI based on the selected action & Worklog status.
   * @param {string} employee_id - The ID of the current employee.
   */
  updateDialogBasedOnAction(employee_id) {
      const action_value = this.dialogUI.get_value("action");
      const isEndOfWork = action_value === ACTIONS.EOW;
      
      if (isEndOfWork) {
          // Refresh allocation status when showing worklog section
          if (this.dialogUI.worklog_data) {
              this.refresh_allocation_status_frontend();
          }
      }
  }

  // Start periodic refresh (every 30 seconds)
  startPeriodicRefresh(employee_id) {
      // clearing existing interval first
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval);
        this.refreshInterval = null;
      }

      this.refreshInterval = setInterval(() => {
          // early stop and return from next interval if dialog is closed
          if (!this.isDialogCurrentlyOpen) {
            this.stopPeriodicRefresh();
            return;
          }

          // Only refresh if dialog is still open and action is End of Work
          const currentAction = this.dialogUI?.get_value("action");
          if (currentAction !== ACTIONS.EOW)
            return;

          this.refresh_allocation_status_from_backend(employee_id);
      }, window.WORK_DURATION_RECALC_INTERVAL_MS);
  }

  // Stop periodic refresh
  stopPeriodicRefresh() {
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval);
        this.refreshInterval = null;
      }
    this.isRefreshing = false;
  }

  // Frontend-only calculation (for real-time updates when typing)
refresh_allocation_status_frontend() {

    const $container = this.dialogUI.fields_dict[FIELD.ALLOCATION_STATUS_CONTAINER]?.$wrapper;
    if (!$container || $container.length === 0) return;
    
    // Get tasks from the table
    const table_field = this.dialogUI.fields_dict[FIELD.TASKS_ENTRY];
    const tasks = table_field?.df?.data || [];
    
    let totalAllocated = 0;
    tasks.forEach(task => {
        totalAllocated += parseFloat(task[FIELD.TIME_SPENT]) || 0;
    });
    
    const currentTotal = parseFloat(this.dialogUI.worklog_data?.[FIELD.TIME_TOTAL_ACTUAL]) || 0;
    const unallocated = currentTotal - totalAllocated;
    const tolerance = (this.dialogUI.worklog_data?.[FIELD.TOLERANCE_MIN] || DEFAULT_TOLERANCE_MINUTES) / 60;
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
            messageHtml = `<span class="text-warning">▼</span> <strong>${unallocated.toFixed(2)}  ${__("hrs")}</strong> ${__("left to allocate")} <span class="text-muted">(${__("within tolerance")} ✓)</span>`;
        } else {
            messageHtml = `<span class="text-warning">▲</span> <strong>${absUnallocated.toFixed(2)} ${__("hrs")}</strong> ${__("overallocated")} <span class="text-muted">(${__("within tolerance")} ✓)</span>`;
        }
    } else {
        statusClass = 'danger';
        if (unallocated > 0) {
            messageHtml = `<span class="text-danger">▼</span> <strong>${unallocated.toFixed(2)}  ${__("hrs")}</strong> ${__("left to allocate")} <span class="text-danger">(${__("exceeds tolerance")} !)</span>`;
        } else {
            messageHtml = `<span class="text-danger">▲</span> <strong>${absUnallocated.toFixed(2)} ${__("hrs")}</strong> ${__("overallocated")} <span class="text-danger">(${__("exceeds tolerance")} !)</span>`;
        }
    }
    
    // Build HTML
    const html = `<div class="allocation-mismatch-indicator allocation-mismatch-${statusClass}"><div class="allocation-mismatch-content">${messageHtml}</div></div>`;
    $container.removeClass('hide-control').show();
    $container.html(html);
}

// Backend-fetched calculation (for periodic refresh)
refresh_allocation_status_from_backend() {

    const employee_id = this.current_employee_id || this.dialogUI.worklog_data?.employee_id;
    if (!employee_id) return;

    if (this.isRefreshing)
      return;

    this.isRefreshing = true;
    

    frappe.call({
        method: API.WORKLOG.PREPARE_CHECKOUT,
        args: { employee_id: employee_id },
        callback: (response) => {
          this.isRefreshing = false;

          if (response?.message) {
            const data = response.message;

            // Update only time-related data
            this.dialogUI.worklog_data[FIELD.TIME_TOTAL_ACTUAL] = data[FIELD.TIME_TOTAL_ACTUAL];
            this.dialogUI.worklog_data[FIELD.TIME_SINCE_SAVE] = data[FIELD.TIME_SINCE_SAVE];
            this.dialogUI.worklog_data[FIELD.TIME_SAVED] = data[FIELD.TIME_SAVED];

            // Refresh allocation status using frontend calculation (preserves user input)
            this.refresh_allocation_status_frontend();
          }
        },
        error: () => {
          this.isRefreshing = false;
        }
    });
}

  /**
   * Initializes the dialog with necessary UI adjustments and event bindings if one is not rendered.
   * @param {string} employee_id - The ID of the current employee.
   */
  initializeDialog(employee_id) {
    // Stop re-initialization of dialog UI if one is already open
    if(this.isDialogCurrentlyOpen) return;
    
    this.dialogUI.show();
    this.isDialogCurrentlyOpen = true;
    
    // Start the interval once when dialog opens to prevent multiple simultaneous calls
    if (!this.isRefreshing) {
      this.startPeriodicRefresh(employee_id);
    }

    // Get everything from one API call
    frappe.call({
        method: API.WORKLOG.GET_CONTEXT,
        args: {
          employee_id: employee_id,
          is_dialog_call: true, // Flag to indicate this call is from dialog initialization
        },
        callback: (response) => {
            if (response.message) {
                const context = response.message;
                this.dialogUI.worklog_context = context;  // Storing context
                
                // Just assign the pre-rendered HTML - no JS strings!
                const $statusContainer = this.dialogUI.fields_dict[FIELD.WORKLOG_STATUS_CONTAINER]?.$wrapper;
                if ($statusContainer) {
                    $statusContainer.html(context.worklog_status_today_html);
                }
                
                // Now load worklog data for tasks (reuse existing function)
                this.loadTasksData(employee_id);
            }
        }
    });
  }

  loadTasksData(employee_id){
    // Store employee_id for periodic refresh
    this.current_employee_id = employee_id;
    
    frappe.call({
      method: API.WORKLOG.PREPARE_CHECKOUT,
      args: { employee_id: employee_id },
      callback: (response) => {
        if (response.message) {
          const data = response.message;
          data.employee_id = employee_id;
          this.dialogUI.worklog_data = data;

          // Store ALL values on the dialog instance
          this.dialogUI[FIELD.TIME_SINCE_SAVE] = data[FIELD.TIME_SINCE_SAVE];
          this.dialogUI[FIELD.WORK_DURATION] = data[FIELD.WORK_DURATION];

          // Update button label based on existing worklog
          const existingWorklogName = data.existing_worklog_name;
          const btnField = this.dialogUI.fields_dict[FIELD.WORKLOG_FULL_FORM_BTN];
          
          if (btnField) {
              if (existingWorklogName) {
                  btnField.df.label = __("Open existing worklog ↗");
              } else {
                  btnField.df.label = __("Enter complete detail ↗");
              }
              // Refresh the button to show new label
              btnField.refresh();
          }

          let formattedTasks

          // Check if there's an existing worklog
          if (data.existing_worklog_name && data[FIELD.EXISTING_TASKS]) {
            // Load existing worklog data into dialog fields

            // Populate simple fields:
            // For the text-only task desc field of the Dialog, handle compatibility by extracting only
            // plain text from worklog form's `work_desc` field which is a text-editor (HTML) wrapper
            if (data.existing_work_desc) {
              // Create a temporary element to extract plain text
              const tempDiv = document.createElement('div');
              tempDiv.innerHTML = data.existing_work_desc;
              const plainText = tempDiv.textContent || tempDiv.innerText || '';
              this.dialogUI.set_value(FIELD.WORKLOG_BOX, plainText.trim());
            }
            if (data.existing_ticket_link) {
              this.dialogUI.set_value([FIELD.EXTERNAL_REFERENCE], data.existing_ticket_link);
            }
            if (data.existing_is_home_office) {
              this.dialogUI.set_value([FIELD.IS_HOME_OFFICE], data.existing_is_home_office);
            }

            // Load tasks from existing_tasks
            formattedTasks = data[FIELD.EXISTING_TASKS].map((task, idx) => ({
              idx: idx + 1,
              name: `row ${idx + 1}`,
              __islocal: true,
              [FIELD.TASK]: task[FIELD.TASK],
              [FIELD.SUBJECT]: task[FIELD.SUBJECT],
              [FIELD.TIME_SPENT]: task[FIELD.TIME_SPENT] || 0,
              [FIELD.EXPECTED_TIME]: task[FIELD.EXPECTED_TIME] || 0,
              [FIELD.STATUS]: __(task[FIELD.STATUS] || ""),
              [FIELD.PROGRESS_INCREMENT]: task[FIELD.PROGRESS_INCREMENT] || 
                (task[FIELD.TIME_SPENT] && task[FIELD.EXPECTED_TIME] ? 
                ((task[FIELD.TIME_SPENT] / task[FIELD.EXPECTED_TIME]) * 100).toFixed(1) : 0),
              [FIELD.TASK_DESC]: task[FIELD.TASK_DESC] || '',
              [FIELD.PRIORITY]: __(task[FIELD.PRIORITY] || '')
            }));
          } else {
            // New worklog - load prefilled tasks
            formattedTasks = (data[FIELD.PREFILLED_TASKS] || []).map((task, idx) => ({
              idx: idx + 1,
              name: `row ${idx + 1}`,
              __islocal: true,
              [FIELD.TASK]: task[FIELD.TASK],
              [FIELD.SUBJECT]: task[FIELD.SUBJECT],
              [FIELD.TIME_SPENT]: 0,
              [FIELD.EXPECTED_TIME]: task[FIELD.EXPECTED_TIME] || 0,
              [FIELD.STATUS]: __(task[FIELD.STATUS] || ""),
              [FIELD.PROGRESS_INCREMENT]: 0,
              [FIELD.TASK_DESC]: '',
              [FIELD.PRIORITY]: __(task[FIELD.PRIORITY] || '')
            }));
          }

          // Set to table
          const table_field = this.dialogUI.fields_dict[FIELD.TASKS_ENTRY];
          if (table_field) {            
            table_field.df.data = Array.isArray(formattedTasks)? formattedTasks: [];
            table_field.grid.refresh();
          }

          // recalculate allocation status on frontend
          this.refresh_allocation_status_frontend();
        }
      }
    })
  }

  /**
   * Submits the check-in action for the employee and updates the dashboard.
   * @param {Object} values - The selected action and other dialog values.
   * @param {string} employee_id - The ID of the current employee.
   */
  submitCheckin(values, employee_id) {
    frappe.call({
      method: API.FLEXTIME.SUBMIT_CHECKIN,
      args: {
        action: values.action,
        employee_id: employee_id,
      },
      callback: (response) => {
        const res = response.message;
        
        // Exit early if there is an error in the response
        if (res.status === 'error') {
          FrappeUtils.toast_failure(res.message || 'failure');
          return;
        }
        
        // Checkin success message from backend
        FrappeUtils.toast_success(res.message || 'success');

        this.refresh_dashboard();
        EasyCheckinStatus.render();

        // Refresh check-in options after any check-in action
        if (window.refreshCheckinOptions) {
          window.refreshCheckinOptions();
        }

        // Hide the dialog and show a success alert
        this.dialogUI.hide();
      },
      error: (error) => {
        console.error("An error occurred when submitting Checkin:", error); // Handle exceptions or any uncaught errors from the backend
        FrappeUtils.toast_failure(error.message);
      }
    });
  }

  /**
   * Adds a new worklog entry for the employee.
   * @param {Object} values - Object containing values entered by the user in the dialog form.
   * @param {string} employee_id - The ID of the current employee.
   * @param {string} work_desc - The text entered in the worklog description field.
   * @param {string} ticket_link - The external reference URL associated with the worklog.
   * @param {string} is_home_office - Is the work done from Home - Yes/No.
  **/
  submitCheckinAfterAddingWorklog(values, employee_id, work_desc, ticket_link, is_home_office) {
  
    // Get tasks from the table
    const table_field = this.dialogUI.fields_dict[FIELD.TASKS_ENTRY];
    const tasks = table_field?.df?.data || [];

    // Prepare tasks data (only needed fields)
    const tasks_entry = tasks.map(t => ({
      task: t.task,
      [FIELD.SUBJECT]: t[FIELD.SUBJECT],
      [FIELD.TIME_SPENT]: parseFloat(t[FIELD.TIME_SPENT]) || 0,
      [FIELD.EXPECTED_TIME]: t[FIELD.EXPECTED_TIME] || 0,
      [FIELD.STATUS]: __(t[FIELD.STATUS] || ""),
      [FIELD.PROGRESS_INCREMENT]: t[FIELD.PROGRESS_INCREMENT] || 0,
      [FIELD.TASK_DESC]: t[FIELD.TASK_DESC],
      [FIELD.PRIORITY]: __(t[FIELD.PRIORITY] || '')
    }));

    // Get existing worklog name (null if none)
    const existing_worklog_name = this.dialogUI.worklog_data?.existing_worklog_name || null;
    // Get current_total from the stored worklog_data
    const current_total = parseFloat(this.dialogUI.worklog_data?.[FIELD.TIME_TOTAL_ACTUAL]) || 0;

    // Build worklog data
    const worklog_data = {
      [FIELD.WORK_DESC]: work_desc,
      [FIELD.IS_HOME_OFFICE]: is_home_office,
      [FIELD.TICKET_LINK]: ticket_link,
      [FIELD.TIME_SAVED]: current_total,
      [FIELD.TASKS_ENTRY]: tasks_entry
    };

    frappe.call({
      method: API.WORKLOG.SAVE_AND_CHECKOUT,  // Use save_and_checkout for updates
      args: {
        worklog_name: existing_worklog_name,  // null for new, name for update
        employee_id: employee_id,
        worklog_data: worklog_data,
        current_total: current_total
      },
      callback: (response) => {
        if (response && response.message.status === 'success') {
          FrappeUtils.toast_success(response.message.message || 'success');
          JsUtils.saveStringToLocalStore(this.PREV_WFH_PREF_KEY, is_home_office);

          if (window.refreshCheckinOptions) {
            window.refreshCheckinOptions();
          }

          this.dialogUI.hide();
        } else {
          FrappeUtils.toast_failure(response.message.message || 'failure');
        }
      },
      error: (error) => {
        console.error("An error occurred when updating Worklog:", error);
        FrappeUtils.toast_failure(error.message);
      }
    });
  }

  /** Refreshes the dashboard UI by triggering the refresh action on the associated buttons. */
  refresh_dashboard() {
    if (this.refresh_buttons === undefined) {
      return;
    }

    for (let button of this.refresh_buttons) {
      button.click();
    }
  }

  /** Binds events for number card of dashboard */
  static prepare_dashboard() {
    
    let dialog = EasyCheckinDialog.singleton();

    document
      .getElementById("hr_time_number_card_checkin_status")
      .querySelector(".checkin_status").onclick = function () {
        dialog.show();
      };

    dialog.refresh_buttons = [
      document
        .querySelector('[number_card_name="Checkin status"]')
        .querySelector('[data-action="action-refresh"]'),
      document
        .querySelector('[number_card_name="Employees present"]')
        .querySelector('[data-action="action-refresh"]'),
      document
        .querySelector('[quick_list_name="Employee Checkin"]')
        .querySelector(".refresh-list.btn"),
    ];

    setTimeout(() => {
      dialog.refresh_dashboard();
    }, window.CHECKIN_STATUS_REFRESH_INTERVAL_MS);
  }

  /** Returns/Creates the singleton instance */
  static singleton() {
    if (window.easy_checkin_dialog === undefined) {
      window.easy_checkin_dialog = new EasyCheckinDialog();
    }

    return window.easy_checkin_dialog;
  }
}