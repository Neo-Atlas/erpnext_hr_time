export class NumberCardUpdater {
    
    /**
     * Update Checkin status card
     */
    static updateCheckinStatus(status, icon, labelWithDuration) {
        const container = document.getElementById('hr_time_number_card_checkin_status');
        if (container) {
            const statusDiv = container.querySelector('.checkin_status');
            if (statusDiv) {
                statusDiv.className = `checkin_status ${status}`;
                
                const iconEl = statusDiv.querySelector('.fa');
                if (iconEl) {
                    iconEl.className = `fa fa-${icon}`;
                }
                
                // Update label (includes duration)
                const labelEl = statusDiv.querySelector('.label');
                if (labelEl) {
                    labelEl.textContent = labelWithDuration;
                }
            }
        }
    }

    /**
     * Update Employees present card
     */
    static updateEmployeesPresent(count) {
        const container = document.getElementById('hr_time_nc_employees_present');
        if (!container) return;
        
        const countDiv = container.querySelector('.count');
        if (countDiv) {
            countDiv.textContent = count;
        }
    }

    /**
     * Update Flextime balance card
     */
    static updateFlextimeBalance(data) {
        const container = document.getElementById('hr_time_dashboard_flextime_balance');
        if (!container) return;
        
        // Update balance section
        const hoursSpan = container.querySelector('.hours');
        const minutesSpan = container.querySelector('.minutes');
        
        if (hoursSpan) {
            hoursSpan.textContent = data.hours_display;
            hoursSpan.className = `${data.color} hours`;
        }
        if (minutesSpan) {
            minutesSpan.textContent = data.minutes_display;
        }
        
        // Update trend section
        const iconDiv = container.querySelector('.trend .icon');
        const trendSpan = container.querySelector('.trend .absolute');
        const metaSpan = container.querySelector('.trend .meta');
        
        if (iconDiv) {
            iconDiv.textContent = data.is_trend_positive ? '↖' : '↙';
        }
        if (trendSpan) {
            trendSpan.textContent = data.trend_display;
        }
        if (metaSpan) {
            metaSpan.textContent = frappe._("Within last month");
        }
    }

    static refreshCheckinStatus() {
        frappe.call({
            method: "hr_time.api.flextime.api.get_checkin_status_data",
            callback: (response) => {
                if (response.message) {
                    this.updateCheckinStatus(
                        response.message.status,
                        response.message.icon,
                        response.message.label_with_duration
                    );
                }
            }
        });
    }

    static refreshFlextimeBalance() {
        frappe.call({
            method: "hr_time.api.flextime.api.get_flextime_balance_data",
            callback: (response) => {
                if (response.message) {
                    this.updateFlextimeBalance(response.message);
                }
            }
        });
    }

    static refreshEmployeesPresentCount() {
        frappe.call({
            method: "hr_time.api.flextime.api.get_employees_present_count",
            callback: (response) => {
                if (response.message?.count !== undefined) {
                    this.updateEmployeesPresent(response.message.count);
                }
            }
        });
    }
}