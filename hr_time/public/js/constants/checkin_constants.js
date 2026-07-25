/**
 * Checkin Status Constants
 * Centralized mapping for UI display across all components
 */
export const CHECKIN_STATUS = {
    IN: {
        key: 'IN',
        class: 'work',
        icon: 'check',
        labelPrefix: 'Checked in',
        description: 'User is actively working'
    },
    BREAK: {
        key: 'BREAK',
        class: 'break',
        icon: 'coffee',
        labelPrefix: 'Break',
        description: 'User is on break'
    },
    OUT: {
        key: 'OUT',
        class: 'out',
        icon: 'remove',
        labelPrefix: 'Checked out',
        description: 'User has ended work'
    },
    UNKNOWN: {
        key: 'UNKNOWN',
        class: 'out',
        icon: 'question',
        labelPrefix: 'Unknown',
        description: 'Status could not be determined'
    }
};

/**
 * Get status config by key
 * @param {string} key - Status key (IN, BREAK, OUT, UNKNOWN)
 * @returns {Object} Status configuration
 */
export function getStatusConfig(key) {
    return CHECKIN_STATUS[key] || CHECKIN_STATUS.UNKNOWN;
}

/**
 * Get all available status keys
 * @returns {string[]} Array of status keys
 */
export function getStatusKeys() {
    return Object.keys(CHECKIN_STATUS);
}

/**
 * Check if status is active (working or on break)
 * @param {string} key - Status key
 * @returns {boolean}
 */
export function isActiveStatus(key) {
    return key === 'IN' || key === 'BREAK';
}