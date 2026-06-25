// src/utils/dateUtils.js

/**
 * Get the date to use for a contract based on filter settings
 * @param {Object} contract - Contract object
 * @param {boolean} useCustomerPoDate - Whether to use customer PO date
 * @returns {string|null} - Date string in YYYY-MM-DD format
 */
export function getContractDate(contract, useCustomerPoDate = false) {
    if (useCustomerPoDate) {
        return contract.customer_po_date || contract.start_date || contract.date;
    }
    return contract.start_date || contract.date;
}

/**
 * Get date range for last N months (excluding future dates)
 * @param {number} months - Number of months to go back (default: 12)
 * @returns {Object} - Object with startDate and endDate
 */
export function getLastNMonthsRange(months = 12) {
    const now = new Date();
    const startDate = new Date();
    startDate.setMonth(now.getMonth() - (months - 1));
    startDate.setHours(0, 0, 0, 0);

    const endDate = new Date();
    endDate.setHours(23, 59, 59, 999);

    return { startDate, endDate };
}

/**
 * Filter contracts for last N months based on start_date or customer PO date
 * @param {Array} contracts - Array of contract objects
 * @param {number} months - Number of months to go back (default: 12)
 * @param {boolean} useCustomerPoDate - Whether to use customer PO date
 * @returns {Array} - Filtered contracts
 */
export function filterContractsLastNMonths(contracts, months = 12, useCustomerPoDate = false) {
    const { startDate, endDate } = getLastNMonthsRange(months);

    return contracts.filter(c => {
        const dateToUse = getContractDate(c, useCustomerPoDate);
        if (!dateToUse) return false;

        const contractDate = new Date(dateToUse);
        // Only include contracts from last N months up to today (no future dates)
        return contractDate >= startDate && contractDate <= endDate;
    });
}

/**
 * Create contract timeline data grouped by month
 * @param {Array} contracts - Array of contract objects
 * @param {number} maxMonths - Maximum number of months to show (default: 12)
 * @param {boolean} useCustomerPoDate - Whether to use customer PO date
 * @returns {Array} - Timeline data with name, count, and revenue
 */
export function createContractTimeline(contracts, maxMonths = 12, useCustomerPoDate = false) {
    const map = new Map();

    contracts.forEach(c => {
        const dateToUse = getContractDate(c, useCustomerPoDate);
        if (!dateToUse) return;

        const month = dateToUse.substring(0, 7);
        const curr = map.get(month) || { count: 0, revenue: 0 };

        map.set(month, {
            count: curr.count + 1,
            revenue: curr.revenue + parseFloat(c.amount || 0)
        });
    });

    const sorted = Array.from(map.entries())
        .sort((a, b) => a[0].localeCompare(b[0]))
        .slice(-maxMonths);

    return sorted.map(([name, d]) => ({
        name,
        count: d.count,
        revenue: d.revenue
    }));
}

/**
 * Check if a date is in the future
 * @param {string} dateString - Date string in YYYY-MM-DD format
 * @returns {boolean} - True if date is in the future
 */
export function isFutureDate(dateString) {
    if (!dateString) return false;
    const date = new Date(dateString);
    const now = new Date();
    now.setHours(23, 59, 59, 999);
    return date > now;
}

/**
 * Format month string for display
 * @param {string} monthString - Month string in YYYY-MM format
 * @returns {string} - Formatted month (e.g., "Jan 2024")
 */
export function formatMonthDisplay(monthString) {
    if (!monthString) return '';
    const [year, month] = monthString.split('-');
    const date = new Date(year, parseInt(month) - 1);
    return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
}