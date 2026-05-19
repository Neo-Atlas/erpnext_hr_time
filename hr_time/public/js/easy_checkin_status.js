import { TimeFormatter } from "./utils/time_formatter.js";
import {EasyCheckinDialog} from "./easy_checkin_dialog";
import { NumberCardUpdater } from "./number_card_updater.js";
import { CheckinTimer } from "./checkin_timer.js";
import { CHECKIN_STATUS, getStatusConfig, isActiveStatus } from "./constants/checkin_constants.js";


export class EasyCheckinStatus {
    static subscribed = false;
    static DRIFT_CORRECTION_INTERVAL_MS = 60_000 * 5; // 5 minutes for local timer correction with backend
    static timer = new CheckinTimer();
    static current_employee_id = null;

    static setCurrentEmployeeId(employee_id) {
        this.current_employee_id = employee_id;
    }

    static getCurrentEmployeeId() {
        return this.current_employee_id;
    }

    static getFormattedLabel() {
        const statusConfig = getStatusConfig(this.timer.status);
        
        let seconds = 0;
        if (this.timer.status === CHECKIN_STATUS.IN.key) {
            seconds = this.timer.getCurrentWorkedSeconds();
        } else if (this.timer.status === CHECKIN_STATUS.BREAK.key) {
            seconds = this.timer.getCurrentBreakSeconds();
        }
        
        return TimeFormatter.formatWithDuration(statusConfig.labelPrefix, seconds);
    }

    static updateNavbar() {        
        // Return early if no employee_id (admin)
        if (!this.current_employee_id) {
            $('.navbar .checkin_status').remove();
            return;
        }

        const statusConfig = getStatusConfig(this.timer.status);
        let label = this.getFormattedLabel();
        
        const html = `<div class="checkin_status ${statusConfig.class}">
                        <i class="fa fa-${statusConfig.icon}"></i>
                        <span class="label">${label}</span>
                      </div>`;
        
        $('.navbar .checkin_status').remove();
        $('.navbar .vertical-bar').after(html);
        $('.navbar .checkin_status').click(() => {
            EasyCheckinDialog.singleton().show();
        });
    }

    static updateCheckinStatusCard() {
        const statusConfig = getStatusConfig(this.timer.status);
        let label = this.getFormattedLabel();
        
        NumberCardUpdater.updateCheckinStatus(
            statusConfig.class,
            statusConfig.icon,
            label
        );
    }

    static updateAllDashboardCards() {
        this.updateCheckinStatusCard();
        NumberCardUpdater.refreshEmployeesPresentCount();
        NumberCardUpdater.refreshFlextimeBalance();
    }

    // Define DOM selectors for refreshable components
    static REFRESH_TARGETS = [
        { selector: '[quick_list_name="Employee Checkin"]', buttonSelector: '.refresh-list.btn' },
        { selector: '[quick_list_name="Latest daily status"]', buttonSelector: '.refresh-list.btn' },
        { selector: '[quick_list_name="Latest Summary"]', buttonSelector: '.refresh-list.btn' }
    ];
    
    static refreshQuickLists() {
        for (const target of this.REFRESH_TARGETS) {
            const container = document.querySelector(target.selector);
            if (container) {
                const refreshBtn = container.querySelector(target.buttonSelector);
                if (refreshBtn && !refreshBtn.disabled) {
                    refreshBtn.click();
                }
            }
        }
    }

    static setupCheckinCardClick() {
        document.body.addEventListener('click', (event) => {
            const statusDiv = event.target.closest('#hr_time_number_card_checkin_status .checkin_status');
            if (statusDiv) {
                EasyCheckinDialog.singleton().show();
            }
        });
    }

    static setupEmployeesPresentCardClick() {
        document.body.addEventListener('click', (event) => {
            const card = event.target.closest('#hr_time_nc_employees_present');
            if (card) {
                const route = frappe.utils.generate_route({
                    type: "report",
                    is_query_report: true,
                    name: "Employees present"
                });
                frappe.set_route(route);
            }
        });
    }

    static init() {
        this.setupCheckinCardClick();
        this.setupEmployeesPresentCardClick();

        // Timer callbacks
        this.timer.onUpdate = (timeData) => {
            this.updateNavbar();
            this.updateCheckinStatusCard();
        };

        this.timer.onStatusChange = (newStatus, data) => {
            // Update UI (all cards and quick lists) immediately when status changes
            this.updateNavbar();
            this.updateAllDashboardCards();
            this.refreshQuickLists();
        };

        // Initial sync with callback
        this.timer.sync(() => {
            this.updateNavbar();
            this.updateCheckinStatusCard();
        });

        // DRIFT-CORRECTION: Periodic sync but only when actively working or on break
        setInterval(() => {
            if (this.timer.status !== CHECKIN_STATUS.OUT.key) {
                this.timer.sync();
            }
        }, this.DRIFT_CORRECTION_INTERVAL_MS);

        this.initRealtime();
    }

    static initRealtime() {
        if (this.subscribed) return;

        frappe.realtime.on("checkin_status_updated", (data) => {
            console.log('data: ',data);

            // Only process if we have an employee_id (non Admin user):
            // then check if this is for the current user, update personal timer
            if (this.current_employee_id && data.employee_id === this.current_employee_id) {
                this.timer.updateFromEvent(data);
                this.updateNavbar();
                this.updateCheckinStatusCard();
            }
            
            // Always update admin-relevant data (employees present count)
            NumberCardUpdater.refreshEmployeesPresentCount();
            
            // Other global updates
            this.refreshQuickLists();

            // Refresh worklog form if open
            const current_route = frappe.get_route();
            if (current_route[0] === 'Form' && current_route[1] === 'Worklog' && cur_frm?.refresh) {
                cur_frm.refresh();
            }

            // Refresh dialog if open
            const dialog = EasyCheckinDialog.singleton();
            if (dialog?.isDialogCurrentlyOpen) {
                console.log('checkin status');
                
                dialog.preloadCheckinOptions();
            }
        });

        this.subscribed = true;
    }
}