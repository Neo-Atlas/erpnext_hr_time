// utils/time_formatter.js
export class TimeFormatter {
    /**
     * Format seconds into hours, minutes, seconds
     * @param {number} seconds - Total seconds
     * @returns {Object} { hours, minutes, seconds, total }
     */
    static formatSeconds(seconds) {
        const hrs = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        return { 
            hours: hrs, 
            minutes: mins, 
            seconds: secs, 
            total: seconds 
        };
    }

    /**
     * Format time as HH:MM (without seconds)
     * @param {number} seconds - Total seconds
     * @returns {string} Formatted time (e.g., "02:30")
     */
    static toShortFormat(seconds) {
        const { hours, minutes } = this.formatSeconds(seconds);
        return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
    }

    /**
     * Format duration for display with label
     * @param {string} labelPrefix - e.g., "Checked in", "Break"
     * @param {number} seconds - Duration in seconds
     * @returns {string} e.g., "Checked in (02:30)"
     */
    static formatWithDuration(labelPrefix, seconds) {
        if (seconds <= 0) return labelPrefix;
        return `${labelPrefix} (${this.toShortFormat(seconds)})`;
    }
}