import { formatCurrency, formatHP } from './api';

/**
 * Generate detailed modal data based on chart type and clicked segment
 */
export function generateModalData(chartType, segment, rawData) {
    let detailedData = [];
    let title = '';

    switch (chartType) {
        case 'Revenue by Vertical':
            detailedData = rawData.contracts
                .filter(c => (c.parent_vertical || 'Uncategorized') === segment.name)
                .map(c => ({
                    'Contract ID': c.name,
                    'Customer': c.customer_name,
                    'Date': c.date,
                    'Amount': formatCurrency(parseFloat(c.amount || 0)),
                    'HP': formatHP(parseFloat(c.total_hp || 0)),
                    'Region': c.region,
                    'Branch': c.branch,
                }));
            title = `${chartType} - ${segment.name} (${detailedData.length} contracts)`;
            break;

        case 'Deal Status Distribution':
            detailedData = rawData.deals
                .filter(d => (d.status || 'Unknown') === segment.name)
                .map(d => ({
                    'Deal ID': d.name,
                    'Customer': d.customer_name,
                    'Register Date': d.register_date,
                    'Status': d.status,
                    'Type': d.deal_type,
                    'Owner': d.owner,
                    'Region': d.region,
                    'Branch': d.branch,
                }));
            title = `${chartType} - ${segment.name} (${detailedData.length} deals)`;
            break;

        case 'Customers by Industry':
            detailedData = rawData.organizations
                .filter(o => (o.industry || 'Uncategorized') === segment.name)
                .map(o => ({
                    'Customer ID': o.name,
                    'Organization': o.organization_name,
                    'HC': o.customer_hc,
                    'Vertical': o.parent_vertical,
                    'Type': o.customer_type,
                    'Region': o.region,
                    'Branch': o.branch,
                }));
            title = `${chartType} - ${segment.name} (${detailedData.length} customers)`;
            break;

        case 'AMC Status Distribution':
            detailedData = rawData.deals
                .filter(d => (d.warranty_amc_status || 'Unknown') === segment.name)
                .map(d => ({
                    'Deal ID': d.name,
                    'Customer': d.customer_name,
                    'AMC Status': d.warranty_amc_status,
                    'Register Date': d.register_date,
                    'Type': d.deal_type,
                    'Owner': d.owner,
                    'Region': d.region,
                    'Branch': d.branch,
                }));
            title = `${chartType} - ${segment.name} (${detailedData.length} deals)`;
            break;

        case 'Quotation Status':
            detailedData = rawData.quotations
                .filter(q => (q.status || 'Unknown') === segment.name)
                .map(q => ({
                    'Quotation ID': q.name,
                    'Customer': q.customer_name,
                    'Date': q.date,
                    'Status': q.status,
                    'Amount': formatCurrency(parseFloat(q.amount || 0)),
                    'HP': formatHP(parseFloat(q.total_hp || 0)),
                    'Region': q.region,
                    'Branch': q.branch,
                }));
            title = `${chartType} - ${segment.name} (${detailedData.length} quotations)`;
            break;

        case 'Deal Type Distribution':
            detailedData = rawData.deals
                .filter(d => (d.deal_type || 'Unknown') === segment.name)
                .map(d => ({
                    'Deal ID': d.name,
                    'Customer': d.customer_name,
                    'Type': d.deal_type,
                    'Status': d.status,
                    'Register Date': d.register_date,
                    'Owner': d.owner,
                    'Region': d.region,
                    'Branch': d.branch,
                }));
            title = `${chartType} - ${segment.name} (${detailedData.length} deals)`;
            break;

        case 'Customer Type Distribution':
            detailedData = rawData.organizations
                .filter(o => (o.customer_type || 'Unknown') === segment.name)
                .map(o => ({
                    'Customer ID': o.name,
                    'Organization': o.organization_name,
                    'Type': o.customer_type,
                    'HC': o.customer_hc,
                    'Industry': o.industry,
                    'Vertical': o.parent_vertical,
                    'Region': o.region,
                    'Branch': o.branch,
                }));
            title = `${chartType} - ${segment.name} (${detailedData.length} customers)`;
            break;

        case 'Revenue by Industry':
        case 'Contract Type Breakdown':
            detailedData = rawData.contracts
                .filter(c => {
                    if (chartType === 'Revenue by Industry') {
                        return (c.industry || 'Uncategorized') === segment.name;
                    } else {
                        return (c.deal_type || 'Standard') === segment.name;
                    }
                })
                .map(c => ({
                    'Contract ID': c.name,
                    'Customer': c.customer_name,
                    'Date': c.date,
                    'Amount': formatCurrency(parseFloat(c.amount || 0)),
                    'HP': formatHP(parseFloat(c.total_hp || 0)),
                    'Type': c.deal_type,
                    'Industry': c.industry,
                    'Region': c.region,
                    'Branch': c.branch,
                }));
            title = `${chartType} - ${segment.name} (${detailedData.length} contracts)`;
            break;

        case 'Contract Timeline':
            detailedData = rawData.contracts
                .filter(c => c.date && c.date.substring(0, 7) === segment.month)
                .map(c => ({
                    'Contract ID': c.name,
                    'Customer': c.customer_name,
                    'Date': c.date,
                    'Amount': formatCurrency(parseFloat(c.amount || 0)),
                    'HP': formatHP(parseFloat(c.total_hp || 0)),
                    'Type': c.deal_type,
                    'Region': c.region,
                    'Branch': c.branch,
                }));
            title = `Contracts in ${segment.month} (${detailedData.length} contracts)`;
            break;

        default:
            title = chartType;
    }

    return { data: detailedData, title };
}

/**
 * Get unique values from array for filter options
 */
export function getUniqueValues(array, key) {
    return Array.from(new Set(array.map(item => item[key]).filter(Boolean))).sort();
}