import { TimeFormatter } from "./utils/time_formatter.js";
import { CHECKIN_STATUS, isActiveStatus } from "./constants/checkin_constants.js";


export class CheckinTimer {

    static UI_REFRESH_INTERVAL_MS = 1000;
    
    constructor() {
        this.baseWorkedSeconds = 0;
        this.baseBreakSeconds = 0;
        this.baseTimestamp = null;
        this.status = CHECKIN_STATUS.OUT.key;
        this.timerInterval = null;
        this.onUpdate = null;
        this.onStatusChange = null;
    }

    updateFromEvent(data) {
        const previousStatus = this.status;
        this.baseWorkedSeconds = data.total_worked_seconds || 0;
        this.baseBreakSeconds = data.total_break_seconds || 0;
        this.baseTimestamp = data.timestamp ? new Date(data.timestamp) : new Date();
        this.status = data.status || CHECKIN_STATUS.OUT.key;
        
        if (isActiveStatus(this.status) && !this.timerInterval) {
            this.startTimer();
        } else if (this.status === CHECKIN_STATUS.OUT.key && this.timerInterval) {
            this.stopTimer();
        }
        
        // Notify of status change
        if (previousStatus !== this.status && this.onStatusChange) {
            this.onStatusChange(this.status, data);
        }
    }

    getCurrentWorkedSeconds() {
        if (this.status === CHECKIN_STATUS.IN.key) {
            const elapsed = (new Date() - this.baseTimestamp) / 1000;
            return Math.max(0, this.baseWorkedSeconds + elapsed);
        }
        return this.baseWorkedSeconds;
    }

    getCurrentBreakSeconds() {
        if (this.status === CHECKIN_STATUS.BREAK.key) {
            const elapsed = (new Date() - this.baseTimestamp) / 1000;
            return this.baseBreakSeconds + elapsed;
        }
        return this.baseBreakSeconds;
    }

    getCurrentSessionFormattedTime() {
        const seconds = this.getCurrentSeconds();
        return TimeFormatter.formatSeconds(seconds);
    }

    getCurrentSeconds() {
        if (this.status === CHECKIN_STATUS.IN.key) return this.getCurrentWorkedSeconds();
        if (this.status === CHECKIN_STATUS.BREAK.key) return this.getCurrentBreakSeconds();
        if (this.status === CHECKIN_STATUS.OUT.key) return 0;
        return 0;
    }

    startTimer() {
        if (this.timerInterval) clearInterval(this.timerInterval);
        this.timerInterval = setInterval(() => {
            if (this.onUpdate) {
                this.onUpdate(this.getCurrentSessionFormattedTime());
            }
        }, CheckinTimer.UI_REFRESH_INTERVAL_MS);
    }

    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    sync(callback = null) {
        frappe.call({
            method: "hr_time.api.flextime.api.get_current_session_state",
            callback: (response) => {
                if (response.message) {
                    // Discard(ignore) stale sync response (and UI update) if a realtime event already moved us to OUT state
                    if (this.status === CHECKIN_STATUS.OUT.key &&
                        response.message.status !== CHECKIN_STATUS.OUT.key) {
                        return;
                    }
                    this.updateFromEvent(response.message);
                    if (callback) callback();
                }
            }
        });
    }
}