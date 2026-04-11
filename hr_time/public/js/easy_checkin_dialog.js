import { EasyCheckinStatus } from "./easy_checkin_status";

/**
 * Class representing the EasyCheckinDialog for managing employee check-ins.
 */
export class EasyCheckinDialog {
  /** 
   * Fixed text definitions for various labels in the Dialog
   * @type {Object<string, string>}
   */
  static LABELS = {
    TITLE: "Easy Checkin",
    PRIMARY_ACTION_BTN: "Submit"
  }

  static WORK_DURATION_RECALC_INTERVAL = 10_000; // 10 seconds

  /** The local Storage key to be used to save/get WFH preference. */
  PREV_WFH_PREF_KEY = HR_TIME?.LS_KEYS?.PREV_WFH_PREF || 'neo_hr_time_last_wfh_value'

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

  /** Predefined Action options for Checkin events */
  static ACTIONS = {
    EOW: 'End of work',
    BRK: 'Break',
    RSM: 'Resume work',
    SOW: 'Start of work'
  };

  constructor() {
    this.isDialogCurrentlyOpen = false;
    this.isRefreshing = false;
    this.refreshInterval = null;
  }

  /** Preloads the current checkin status */
  async preloadCheckinOptions() {
    try {
      const response = await frappe.call({
        method: "hr_time.api.flextime.api.get_easy_checkin_options",
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
      // this.checkWorklogsThenCreateDialog(employee_id); // Call the next step if employee ID is available
    } catch (error) {
      FrappeUtils.throw_error_msg(MESSAGES.NOT_FOUND_EMPLOYEE_ID); // Show error message if no employee ID
      console.error(MESSAGES.ERR_GET_EMPLOYEE_ID, error);
    }
  }

  // #1
  async get_prefilled_tasks() {
    try {
      const response = await frappe.call({
        method: "hr_time.api.worklog.api.get_tasks_for_user",
        args: { user: frappe.session.user }
      });
      
      // Format tasks for the table
      return (response.message || []).map(task => ({
        task: task.name,
        task_subject: task.task_subject,
        expected_time: task.expected_time || 0,
        time_spent: 0,
        task_status: task.task_status || 'Open',
        progress_increment: 0
      }));
    } catch (error) {
      console.error("Error prefilling tasks:", error);
      return [];
    }
  }

  // Add event listener for table changes
  setup_table_listeners() {
    this.dialogUI.fields_dict.tasks_entry.grid.wrapper.on('change', ':input', () => {
      this.calculate_totals();
    });
  }

  /**
   * Creates and displays the check-in dialog with options and actions.
   * @param {string} employee_id - The ID of the employee to create Checkin actions for.
   */
  createCheckinDialog(employee_id) {    
    const lastHomeOfficeValue = JsUtils.getStringFromLocalStore(this.PREV_WFH_PREF_KEY);
    
    this.dialogUI = new frappe.ui.Dialog({
      title: __(EasyCheckinDialog.LABELS.TITLE),
      fields: this.getDialogFields(employee_id, lastHomeOfficeValue),
      size: "large",
      primary_action_label: __(EasyCheckinDialog.LABELS.PRIMARY_ACTION_BTN, undefined, "checkin"),
      primary_action: (values) => {
        const actionValue = values.action;
        const worklog_text = this.dialogUI.get_value("worklog_box");
        const trimmed_worklog_text = worklog_text ? worklog_text.trim() : '';
        
        // Derive hasWorklogs from context (if available) or default to false
        const hasWorklogs = !!this.dialogUI.worklog_context?.today_worklog_name;

        // Submit only Checkin for actions other than 'End of work' OR if 'Task Description' is empty when Checking out
        if(actionValue !== EasyCheckinDialog.ACTIONS.EOW || !trimmed_worklog_text){
          if (actionValue === EasyCheckinDialog.ACTIONS.EOW && !hasWorklogs) {
            FrappeUtils.warn_user(MESSAGES.EMPTY_TASK_DESC_WHEN_WORKLOGS);
            return;
          }
          this.submitCheckin(values, employee_id);
        }else{
          const ticket_link = this.dialogUI.get_value("external_reference").trim();
          const is_home_office = this.dialogUI.get_value("is_home_office");
          this.submitCheckinAfterAddingWorklog(values, employee_id, trimmed_worklog_text, ticket_link,
            is_home_office);
        }
      },
      onhide: () => {
        console.log('closing dialog');
        this.isDialogCurrentlyOpen = false;
        this.stopPeriodicRefresh();  // Stop periodic refresh when leaving End of Work
      }
    });

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
        depends_on: `eval: doc.action === '${EasyCheckinDialog.ACTIONS.EOW}'`,
      },
      {
        fieldname: "worklog_status_container",
        fieldtype: "HTML",
        label: "",
        depends_on: `eval: doc.action === '${EasyCheckinDialog.ACTIONS.EOW}'`,
      },
      {
        fieldname: "worklog_box",
        fieldtype: "Text",
        label: "Add Worklog",
        placeholder: "Summarize your task here",
        depends_on: `eval: doc.action === '${EasyCheckinDialog.ACTIONS.EOW}'`,
      },
      {
        fieldname: "tasks_entry",
        fieldtype: "Table",
        label: "Allocate hours",
        options: "Worklog Tasks",
        depends_on: `eval: doc.action === '${EasyCheckinDialog.ACTIONS.EOW}'`,
        reqd: 0,
        fields: [
          {
            fieldname: "task",
            fieldtype: "Link",
            options: "Task",
            in_list_view: 1,
            label: "Ticket",
            reqd: 1,
            columns: 3,
            fetch_from: "task.subject",
            fetch_if_empty: true,
            get_query: () => {
              console.log('getting query');
              // Get already selected tasks from the table
              const table_field = this.dialogUI.fields_dict.tasks_entry;
              const existing_tasks = (table_field?.df?.data || [])
                  .map(row => row.task)
                  .filter(Boolean);

              // ✅ Use global cached value
              const buffer_task_id = window.BUFFER_TASK_ID || '';
              
              return {
                filters: {
                    name: ["not in", [...existing_tasks, buffer_task_id]],
                }
              }
            },
            onchange: function(e) {
              console.log('task changed: ',e);
              const grid_context = this;

              const row = this.doc;
              if (row.task) {
                  // Fetch task details
                  frappe.call({
                      method: "frappe.client.get",
                      args: {
                          doctype: "Task",
                          name: row.task
                      },
                      callback: function(r) {
                        const data = r.message || {}
                          if (data) {
                            console.log(data);
                            console.log('row: ',row);
                            
                            row.task_subject = data.subject
                            row.expected_time = data.expected_time || 0
                            row.priority = data.priority || ""
                            row.task_status =  data.status || "Open"
                              console.log('grid_context: ',grid_context);
                              
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
            fieldname: "task_subject",
            fieldtype: "Data",
            label: "Ticket Name",
            read_only: 1,
            in_list_view: 1,
            columns: 5,
          },
          {
            fieldname: "expected_time",
            fieldtype: "Float",
            label: "Est. Time (hrs)",
            read_only: 1,
            in_list_view: 0,
            columns: 1,
            precision: 2,
            fetch_from: "task.expected_time"
          },
          {
            fieldname: "time_spent",
            fieldtype: "Float",
            label: "Time Spent (hrs)",
            in_list_view: 1,
            columns: 2,
            reqd: 1,
            precision: 2,
            onchange: function () {
              const row = this.doc;
              if (!row.expected_time || row.expected_time === 0) return;

              const value = (row.time_spent / row.expected_time) * 100;
              row.progress_increment = value

              // Refresh depending on context
              if(this.grid){
                // Grid inline edit
                this.grid.refresh();
              }else if (this.layout?.refresh) {
                // Edit row dialog form
                this.layout.refresh();
              }

              // ✅ Update the allocation status display
              const dialog = window.easy_checkin_dialog;
              if (dialog && dialog.refresh_allocation_status_frontend) {
                console.log('refreshing remaining display');
                dialog.refresh_allocation_status_frontend()
              }
            }
          },
          {
            fieldname: "task_status",
            fieldtype: "Data",
            label: "Status",
            read_only: 1,
            in_list_view: 0,
            columns: 1,
            fetch_from: "task.status"
          },
          {
            fieldname: "priority",
            fieldtype: "Data",
            label: "Priority",
            read_only: 1,
            in_list_view: 0,
            columns: 1,
            fetch_from: "task.priority"
          },
          {
            fieldname: "progress_increment",
            fieldtype: "Percent",
            label: "Progress Added",
            read_only: 1,
            in_list_view: 0,
            columns: 2,
            precision: 1
          }
        ],
        data: [], // Will be populated dynamically
        get_data: () => {
            // ✅ Always return an array
            const tasks = this.dialogUI?.worklog_data?.existing_tasks || 
                          this.dialogUI?.worklog_data?.prefilled_tasks || [];
            return Array.isArray(tasks) ? tasks : [];
        }
      },
      {
        fieldname: "allocation_status_container",
        fieldtype: "HTML",
        depends_on: `eval: doc.action === '${EasyCheckinDialog.ACTIONS.EOW}'`,
      },
      {
        label: "External Reference",
        fieldname: "external_reference",
        fieldtype: "Data",
        options: "URL", // Validate as a URL
        placeholder: __("e.g. link to a ticket in an external system"),
        depends_on: `eval: doc.action === '${EasyCheckinDialog.ACTIONS.EOW}'`,
        reqd: false,
      },
      {
        label: "Home Office",
        fieldname: "is_home_office",
        fieldtype: "Select",
        default: lastHomeOfficeValue,
        depends_on: `eval: doc.action === '${EasyCheckinDialog.ACTIONS.EOW}'`,
        placeholder: __("Yes/No"),
        options: "\nYes\nNo",
      },
      {
        fieldname: "worklog_full_form_btn",
        fieldtype: "Button",
        label: "Enter complete detail ↗",
        depends_on: `eval: doc.action === '${EasyCheckinDialog.ACTIONS.EOW}'`,
        click: () => {
            const existingWorklogName = this.dialogUI.worklog_data?.existing_worklog_name;

            // Get all dialog values
            const taskDesc = this.dialogUI.get_value('worklog_box') || '';
            const ticket_link = this.dialogUI.get_value("external_reference")?.trim() || '';
            const is_home_office = this.dialogUI.get_value("is_home_office") || '';

            // ✅ Get tasks from the table
            const table_field = this.dialogUI.fields_dict.tasks_entry;
            const tasks = table_field?.df?.data || [];
            
            if(is_home_office){
                JsUtils.saveStringToLocalStore(this.PREV_WFH_PREF_KEY, is_home_office);
            }
            
            // Format tasks for worklog form
            // tasks.some((task)=>task.time_spent>0)
            const tasks_entry = tasks.map(task => ({
                task: task.task,
                task_subject: task.task_subject,
                expected_time: task.expected_time || 0,
                time_spent: parseFloat(task.time_spent) || 0,
                progress_increment: task.progress_increment || 0,
                task_status: task.task_status || 'Open',
                description: task.description || '',
                priority: task.priority || ''
            }));

            if (existingWorklogName) {
                // Open existing worklog
                frappe.set_route('Form', 'Worklog', existingWorklogName);
            }else{
              console.log('opening new: ',taskDesc+' '+is_home_office);
              
              frappe.new_doc("Worklog", {
                  task_desc: taskDesc,
                  ticket_link: ticket_link,
                  is_home_office: is_home_office,
                  // tasks_entry: tasks_entry || []  // ✅ Preserve task allocations
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
      const isEndOfWork = action_value === EasyCheckinDialog.ACTIONS.EOW;
      console.log('isEndOfWork: ',isEndOfWork);
      
      if (isEndOfWork) {
          // Refresh allocation status when showing worklog section
          if (this.dialogUI.worklog_data) {
              this.refresh_allocation_status_frontend();
          }
      }
  }

  // Start periodic refresh (every 30 seconds)
  startPeriodicRefresh(employee_id) {
      console.log('startPeriodicRefresh ing');
      // clearing existing interval first
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval);
        this.refreshInterval = null;
      }

      this.refreshInterval = setInterval(() => {
          // early stop and return from next interval if dialog is closed
          if (!this.isDialogCurrentlyOpen) {
            console.log('Dialog closed, stopping refresh');
            this.stopPeriodicRefresh();
            return;
          }

          // Only refresh if dialog is still open and action is End of Work
          const currentAction = this.dialogUI?.get_value('action');
          if (currentAction !== EasyCheckinDialog.ACTIONS.EOW) {
            console.log('Periodic refresh: Not EOW, skipping');
            return;
          }

          this.refresh_allocation_status_from_backend(employee_id);
          // }
      }, EasyCheckinDialog.WORK_DURATION_RECALC_INTERVAL);
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
    console.log('refresh_allocation_status_frontend - frontend calculation');
    
    const $container = this.dialogUI.fields_dict.allocation_status_container?.$wrapper;
    if (!$container || $container.length === 0) return;
    
    // Get tasks from the table
    const table_field = this.dialogUI.fields_dict.tasks_entry;
    const tasks = table_field?.df?.data || [];
    
    let totalAllocated = 0;
    tasks.forEach(task => {
        totalAllocated += parseFloat(task.time_spent) || 0;
    });
    
    const currentTotal = parseFloat(this.dialogUI.worklog_data?.time_total_actual) || 0;
    const unallocated = currentTotal - totalAllocated;
    const tolerance = (this.dialogUI.worklog_data?.tolerance_minutes || 30) / 60;
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
    
    // Build HTML
    const html = `<div class="allocation-mismatch-indicator allocation-mismatch-${statusClass}"><div class="allocation-mismatch-content">${messageHtml}</div></div>`;
    $container.removeClass('hide-control').show();
    $container.html(html);
}

// Backend-fetched calculation (for periodic refresh)
refresh_allocation_status_from_backend() {
    console.log('refresh_allocation_status_from_backend - fetching from server');

    const employee_id = this.current_employee_id || this.dialogUI.worklog_data?.employee_id;
    if (!employee_id) return;

    if (this.isRefreshing) {
      console.log('Refresh already in progress, skipping');
      return;
    }
    this.isRefreshing = true;
    

    frappe.call({
        method: "hr_time.api.worklog.api.prepare_worklog_for_checkout",
        args: { employee_id: employee_id },
        callback: (response) => {
          this.isRefreshing = false;

          if (response?.message) {
            const data = response.message;

            // ✅ Update only time-related data
            this.dialogUI.worklog_data.time_total_actual = data.time_total_actual;
            this.dialogUI.worklog_data.time_since_last_save = data.time_since_last_save;
            this.dialogUI.worklog_data.time_saved = data.time_saved;

            // ✅ Refresh allocation status using frontend calculation (preserves user input)
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
    console.log('initializing dialog');
    // Stop re-initialization of dialog UI if one is already open
    if(this.isDialogCurrentlyOpen) return;
    
    this.dialogUI.show();
    this.isDialogCurrentlyOpen = true;
    
    // ✅ Start the interval once when dialog opens
    // ✅ Prevent multiple simultaneous calls
    if (!this.isRefreshing) {
      console.log('Refresh already in progress, skipping');
      // this.isRefreshing = true;
      this.startPeriodicRefresh(employee_id);
      // return;
    }

    // Get everything from one API call
    frappe.call({
        method: "hr_time.api.worklog.api.get_worklog_context",
        args: { employee_id: employee_id },
        callback: (response) => {
            if (response.message) {
                const context = response.message;
                this.dialogUI.worklog_context = context;  // Store context
                
                // ✅ Just assign the pre-rendered HTML - no JS strings!
                const $statusContainer = this.dialogUI.fields_dict.worklog_status_container?.$wrapper;
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
    console.log('loadTasksData');
    // Store employee_id for periodic refresh
    this.current_employee_id = employee_id;
    
    frappe.call({
      method: "hr_time.api.worklog.api.prepare_worklog_for_checkout",
      args: { employee_id: employee_id },
      callback: (response) => {
        if (response.message) {
          const data = response.message;
          console.log('data in dialog: ',data);
          data.employee_id = employee_id;
          this.dialogUI.worklog_data = data;

          // Store ALL values on the dialog instance
          this.dialogUI.time_since_last_save = data.time_since_last_save;
          this.dialogUI.work_duration = data.work_duration;


                          // ✅ Update button label based on existing worklog
          const existingWorklogName = data.existing_worklog_name;
          const btnField = this.dialogUI.fields_dict.worklog_full_form_btn;
          
          if (btnField) {
              if (existingWorklogName) {
                  btnField.df.label = "Open existing worklog  ↗";
              } else {
                  btnField.df.label = "Enter complete detail ↗";
              }
              // Refresh the button to show new label
              btnField.refresh();
          }

          console.log('Worklog data loaded:', data);
          let formattedTasks

          // Check if there's an existing worklog
          if (data.existing_worklog_name && data.existing_tasks) {
            // Load existing worklog data into dialog fields
            console.log('Loading existing worklog:', data.existing_worklog_name);

            // Populate simple fields:
            // For the text-only task desc field of the Dialog, handle compatibility by extracting only
            // plain text from worklog form's `task_desc` field which is a text-editor (HTML) wrapper
            if (data.existing_task_desc) {
              // Create a temporary element to extract plain text
              const tempDiv = document.createElement('div');
              tempDiv.innerHTML = data.existing_task_desc;
              const plainText = tempDiv.textContent || tempDiv.innerText || '';
              this.dialogUI.set_value('worklog_box', plainText.trim());
            }
            if (data.existing_ticket_link) {
              this.dialogUI.set_value('external_reference', data.existing_ticket_link);
            }
            if (data.existing_is_home_office) {
              this.dialogUI.set_value('is_home_office', data.existing_is_home_office);
            }

            // Load tasks from existing_tasks
            formattedTasks = data.existing_tasks.map((task, idx) => ({
              idx: idx + 1,
              name: `row ${idx + 1}`,
              __islocal: true,
              task: task.task,
              task_subject: task.task_subject,
              time_spent: task.time_spent || 0,
              expected_time: task.expected_time || 0,
              task_status: task.task_status || 'Open',
              progress_increment: task.progress_increment || 
                (task.time_spent && task.expected_time ? 
                ((task.time_spent / task.expected_time) * 100).toFixed(1) : 0),
              description: task.description || '',
              priority: task.priority || ''
            }));
          } else {
            // New worklog - load prefilled tasks
            formattedTasks = (data.prefilled_tasks || []).map((task, idx) => ({
              idx: idx + 1,
              name: `row ${idx + 1}`,
              __islocal: true,
              task: task.task,
              task_subject: task.task_subject,
              time_spent: 0,
              expected_time: task.expected_time || 0,
              task_status: task.task_status || 'Open',
              progress_increment: 0,
              description: '',
              priority: task.priority || ''
            }));
          }

          // Set to table
          const table_field = this.dialogUI.fields_dict.tasks_entry;
          if (table_field) {            
            table_field.df.data = Array.isArray(formattedTasks)? formattedTasks: [];
            table_field.grid.refresh();
          }

          // ✅ Instead, calculate allocation status on frontend
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
      method: "hr_time.api.flextime.api.submit_easy_checkin",
      args: {
        action: values.action,
        employee_id: employee_id,
      },
      callback: (response) => {
        // Exit early if there is an error in the response
        if (response && typeof response.message === 'object' && response.message.status === 'error') {
          FrappeUtils.alert_failure(response.message.message)
          return;
        }

        this.refresh_dashboard();
        EasyCheckinStatus.render();

        let message;        

        // Check the action and set the appropriate message
        switch (values.action) {
          case EasyCheckinDialog.ACTIONS.BRK:
            message = MESSAGES.SUCCESS_BREAK;
            break;
          case EasyCheckinDialog.ACTIONS.EOW:
            message = MESSAGES.SUCCESS_CHECKOUT;
            break;
          case EasyCheckinDialog.ACTIONS.RSM:
            message = MESSAGES.SUCCESS_RESUME;
            break;
          case EasyCheckinDialog.ACTIONS.SOW:
            message = MESSAGES.SUCCESS_CHECKIN;
            break;
          default:
            return; // Exit if none of the expected actions match
        }

        // ✅ Refresh check-in options after any check-in action
        if (window.refreshCheckinOptions) {
            window.refreshCheckinOptions();
        }

        // Hide the dialog and show a success alert
        this.dialogUI.hide();
        FrappeUtils.alert_success(message);
      },
      error: (error) => {
        console.error("An error occurred when submitting Checkin:", error); // Handle exceptions or any uncaught errors from the backend
        FrappeUtils.alert_failure(error.message);
      }
    });
  }

  /**
   * Adds a new worklog entry for the employee.
   * @param {Object} values - Object containing values entered by the user in the dialog form.
   * @param {string} employee_id - The ID of the current employee.
   * @param {string} worklog_text - The text entered in the worklog description field.
   * @param {string} ticket_link - The external reference URL associated with the worklog.
   * @param {string} is_home_office - Is the work done from Home - Yes/No.
  **/
  submitCheckinAfterAddingWorklog(values, employee_id, worklog_text, ticket_link, is_home_office) {
  
    // Get tasks from the table
    const table_field = this.dialogUI.fields_dict.tasks_entry;
    const tasks = table_field?.df?.data || [];

    // Prepare tasks data (only needed fields)
    const tasks_entry = tasks.map(t => ({
      task: t.task,
      task_subject: t.task_subject,
      time_spent: parseFloat(t.time_spent) || 0,
      expected_time: t.expected_time || 0,
      task_status: t.task_status || 'Open',
      progress_increment: t.progress_increment || 0,
      description: t.description,
      priority: t.priority
    }));

    // Get existing worklog name (null if none)
    const existing_worklog_name = this.dialogUI.worklog_data?.existing_worklog_name || null;
    // Get current_total from the stored worklog_data
    const current_total = parseFloat(this.dialogUI.worklog_data?.time_total_actual) || 0;

    // Build worklog data
    const worklog_data = {
      task_desc: worklog_text,
      is_home_office: is_home_office,
      ticket_link: ticket_link,
      time_saved: current_total,
      tasks_entry: tasks_entry
    };

    frappe.call({
      method: "hr_time.api.worklog.api.save_and_checkout",  // Use save_and_checkout for updates
      args: {
        worklog_name: existing_worklog_name,  // null for new, name for update
        employee_id: employee_id,
        worklog_data: worklog_data,
        current_total: current_total
      },
      callback: (response) => {
        if (response && response.message) {
          if (response.message.success) {
            FrappeUtils.alert_success(MESSAGES.SUCCESS_WORKLOG_ADDITION);
            JsUtils.saveStringToLocalStore(this.PREV_WFH_PREF_KEY, is_home_office);

            if (window.refreshCheckinOptions) {
              window.refreshCheckinOptions();
            }

            this.dialogUI.hide();
          } else {
            FrappeUtils.alert_failure(response.message.error || MESSAGES.FAILED_CHECKOUT);
          }
        }
      },
      error: (error) => {
        console.error("An error occurred when updating Worklog:", error);
        FrappeUtils.alert_failure(error.message);
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
    console.log('preparing _dashboard');
    
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