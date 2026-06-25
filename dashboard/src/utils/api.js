// Frappe v15 API Integration Utilities

const FRAPPE_URL = import.meta.env.VITE_FRAPPE_URL || 'https://your-frappe-instance.com';
const API_KEY = import.meta.env.VITE_API_KEY;
const API_SECRET = import.meta.env.VITE_API_SECRET;
const DEBUG = import.meta.env.VITE_DEBUG === 'true';

/**
 * Debug logger - only logs when DEBUG is true
 */
function debugLog(message, data) {
    if (DEBUG) {
        console.log(`[Dashboard Debug] ${message}`, data);
    }
}

/**
 * Generic function to fetch data from Frappe
 */
export async function fetchFrappeData(doctype, fields = [], filters = {}, limit = 0) {
    const params = new URLSearchParams({
        fields: JSON.stringify(fields),
        filters: JSON.stringify(filters),
    });

    if (limit > 0) {
        params.append('limit_page_length', limit);
    } else {
        // Fetch all records by setting a very high limit
        params.append('limit_page_length', 99999);
    }

    const url = `${FRAPPE_URL}/api/resource/${doctype}?${params}`;

    debugLog(`Fetching ${doctype}`, { url, filters, fields });

    const response = await fetch(url, {
        headers: {
            'Authorization': `token ${API_KEY}:${API_SECRET}`,
            'Content-Type': 'application/json',
        },
    });

    if (!response.ok) {
        throw new Error(`Failed to fetch ${doctype}: ${response.statusText}`);
    }

    const data = await response.json();
    const result = data.data || [];

    debugLog(`Fetched ${doctype}`, { count: result.length, sample: result[0] });

    return result;
}

/**
 * Call a Frappe method
 */
export async function callFrappeMethod(method, args = {}) {
    const url = `${FRAPPE_URL}/api/method/${method}`;

    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Authorization': `token ${API_KEY}:${API_SECRET}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(args),
    });

    if (!response.ok) {
        throw new Error(`Failed to call method ${method}: ${response.statusText}`);
    }

    const data = await response.json();
    return data.message || data;
}

/**
 * Get All India (Country Level) Data
 */
export async function getCountryData(filters = {}) {
    try {
        debugLog('getCountryData called with filters', filters);

        // Fetch all data in parallel
        // Fetch ALL contracts (remove docstatus filter to show all, not just submitted)
        const contractFilters = {}; // Changed: No docstatus filter
        const quotationFilters = { docstatus: 1 }; // Keep for quotations

        // Apply additional filters only if they exist
        if (filters.date) {
            contractFilters.date = filters.date;
            quotationFilters.date = filters.date;
        }

        const [contracts, deals, organizations, quotations, regions] = await Promise.all([
            fetchFrappeData('CRM Contract', [
                'name', 'customer', 'customer_name', 'region', 'branch',
                'date', 'amount', 'total_usd', 'start_date', 'expiry_date',
                'total_hp', 'currency', 'docstatus', 'industry', 'parent_vertical', 'deal_type', "custom_contract_status"
            ], contractFilters),
            fetchFrappeData('CRM Deal', [
                'name', 'customer', 'customer_name', 'region', 'branch',
                'register_date', 'annual_revenue', 'status', 'deal_type',
                'warranty_amc_status', 'owner', 'industry', 'parent_vertical'
            ], {}), // No filters for deals
            fetchFrappeData('CRM Organization', [
                'name', 'organization_name', 'customer_hc', 'region',
                'branch', 'industry', 'parent_vertical', 'customer_type'
            ], {}), // No filters for organizations
            fetchFrappeData('CRM Quotation', [
                'name', 'customer', 'customer_name', 'region', 'branch',
                'date', 'status', 'amount', 'total_usd', 'total_hp',
                'docstatus'
            ], quotationFilters),
            fetchFrappeData('Region Master', [
                'name', 'region_name', 'region_head', 'region_head_name'
            ], {}),
        ]);

        debugLog('Data fetched', {
            contracts: contracts.length,
            deals: deals.length,
            organizations: organizations.length,
            quotations: quotations.length,
            regions: regions.length
        });

        // Aggregate data by region
        const regionMap = new Map();

        regions.forEach(region => {
            regionMap.set(region.name, {
                regionId: region.name,
                regionName: region.region_name,
                regionHead: region.region_head_name || region.region_head,
                revenue: 0,
                contracts: 0,
                deals: 0,
                amcRenewal: 0,
                warrantyConversion: 0,
                lostAmcConversion: 0,
                lostWarrantyConversion: 0,
                customers: new Set(),
                quotations: 0,
                totalHP: 0,
                contractsList: [],
                dealsList: [],
                quotationsList: [],
            });
        });

        // Aggregate contracts by region
        contracts.forEach(contract => {
            if (contract.region && regionMap.has(contract.region)) {
                const region = regionMap.get(contract.region);
                region.revenue += parseFloat(contract.amount || 0);
                region.contracts += 1;
                region.totalHP += parseFloat(contract.total_hp || 0);

                const type = (contract.deal_type || "")
                    .toLowerCase()
                    .trim();

                if (type === "amc renewal") {
                    region.amcRenewal++;
                }
                else if (type === "warranty conversion" || type === "warranty amc conversion") {
                    region.warrantyConversion++;
                }
                else if (type === "lost amc conversion") {
                    region.lostAmcConversion++;
                }
                else if (type === "lost warranty conversion") {
                    region.lostWarrantyConversion++;
                }

                region.contractsList.push(contract);
                if (contract.customer) {
                    region.customers.add(contract.customer);
                }
            }
        });

        // Aggregate deals by region
        deals.forEach(deal => {
            if (deal.region && regionMap.has(deal.region)) {
                const region = regionMap.get(deal.region);
                region.deals += 1;
                region.dealsList.push(deal);
            }
        });

        // Aggregate quotations by region
        quotations.forEach(quote => {
            if (quote.region && regionMap.has(quote.region)) {
                const region = regionMap.get(quote.region);
                region.quotations += 1;
                region.quotationsList.push(quote);
            }
        });

        // Convert Set to count for customers
        regionMap.forEach(region => {
            region.customers = region.customers.size;
        });

        // Calculate totals
        const regionData = Array.from(regionMap.values());
        const totalRevenue = contracts.reduce((sum, c) => sum + parseFloat(c.amount || 0), 0);
        const totalContracts = contracts.length;
        const totalCustomers = organizations.length;
        const totalDeals = deals.length;
        const totalQuotations = quotations.length;
        const totalHP = contracts.reduce((sum, c) => sum + parseFloat(c.total_hp || 0), 0);

        debugLog('Aggregated totals', {
            totalRevenue,
            totalContracts,
            totalCustomers,
            totalDeals,
            totalQuotations,
            totalHP
        });

        return {
            regions: regionData,
            summary: {
                totalRevenue,
                totalContracts,
                totalCustomers,
                totalDeals,
                totalQuotations,
                totalHP,
                avgContractValue: totalContracts > 0 ? totalRevenue / totalContracts : 0,
            },
            rawData: {
                contracts,
                deals,
                organizations,
                quotations,
            },
        };
    } catch (error) {
        console.error('Error fetching country data:', error);
        throw error;
    }
}

/**
 * Get Region Level Data
 */
export async function getRegionData(regionId, filters = {}) {
    try {
        debugLog('getRegionData called', { regionId, filters });

        const REGION_GROUPS = {
            "NORTH": ["NORTH", "NORTH-1", "NORTH-2"],
            "EAST": ["EAST", "EAST-1", "EAST-2"],
        };

        const regionFilterValue = REGION_GROUPS[regionId]
            ? ["in", REGION_GROUPS[regionId]]
            : regionId;

        const contractFilters = { region: regionFilterValue };
        const quotationFilters = { region: regionFilterValue, docstatus: 1 };
        const dealFilters = { region: regionFilterValue };
        const orgFilters = { region: regionFilterValue };

        if (filters.date) {
            contractFilters.date = filters.date;
            quotationFilters.date = filters.date;
        }

        // Fetch all data for this region
        const [contracts, deals, organizations, quotations, branches] = await Promise.all([
            fetchFrappeData('CRM Contract', [
                'name', 'customer', 'customer_name', 'region', 'branch',
                'date', 'amount', 'total_usd', 'start_date', 'expiry_date',
                'total_hp', 'currency', 'docstatus', 'industry', 'parent_vertical', 'deal_type', "custom_contract_status"
            ], contractFilters),
            fetchFrappeData('CRM Deal', [
                'name', 'customer', 'customer_name', 'region', 'branch',
                'register_date', 'annual_revenue', 'status', 'deal_type',
                'warranty_amc_status', 'owner'
            ], dealFilters),
            fetchFrappeData('CRM Organization', [
                'name', 'organization_name', 'customer_hc', 'region',
                'branch', 'industry', 'parent_vertical', 'customer_type'
            ], orgFilters),
            fetchFrappeData('CRM Quotation', [
                'name', 'customer', 'customer_name', 'region', 'branch',
                'date', 'status', 'amount', 'total_usd', 'total_hp',
                'docstatus'
            ], quotationFilters),
            fetchFrappeData('Region Branches', [
                'name', 'branch_id', 'branch_name', 'branch_head',
                'branch_head_name', 'region'
            ], { region: regionFilterValue }),
        ]);

        debugLog('Region data fetched', {
            contracts: contracts.length,
            deals: deals.length,
            organizations: organizations.length,
            quotations: quotations.length,
            branches: branches.length
        });

        // Aggregate data by branch
        const branchMap = new Map();

        branches.forEach(branch => {
            branchMap.set(branch.name, {
                branchId: branch.name,
                branchName: branch.branch_name,
                branchHead: branch.branch_head_name || branch.branch_head,
                revenue: 0,
                contracts: 0,
                deals: 0,
                customers: new Set(),
                quotations: 0,
                totalHP: 0,
                contractsList: [],
                dealsList: [],
                quotationsList: [],
            });
        });

        // Aggregate contracts by branch
        contracts.forEach(contract => {
            if (contract.branch && branchMap.has(contract.branch)) {
                const branch = branchMap.get(contract.branch);
                branch.revenue += parseFloat(contract.amount || 0);
                branch.contracts += 1;
                branch.totalHP += parseFloat(contract.total_hp || 0);
                branch.contractsList.push(contract);
                if (contract.customer) {
                    branch.customers.add(contract.customer);
                }
            }
        });

        // Aggregate deals by branch
        deals.forEach(deal => {
            if (deal.branch && branchMap.has(deal.branch)) {
                const branch = branchMap.get(deal.branch);
                branch.deals += 1;
                branch.dealsList.push(deal);
            }
        });

        // Aggregate quotations by branch
        quotations.forEach(quote => {
            if (quote.branch && branchMap.has(quote.branch)) {
                const branch = branchMap.get(quote.branch);
                branch.quotations += 1;
                branch.quotationsList.push(quote);
            }
        });

        // Convert Set to count for customers
        branchMap.forEach(branch => {
            branch.customers = branch.customers.size;
        });

        // Calculate totals
        const branchData = Array.from(branchMap.values());
        const totalRevenue = contracts.reduce((sum, c) => sum + parseFloat(c.amount || 0), 0);
        const totalContracts = contracts.length;
        const totalCustomers = organizations.length;
        const totalDeals = deals.length;
        const totalQuotations = quotations.length;
        const totalHP = contracts.reduce((sum, c) => sum + parseFloat(c.total_hp || 0), 0);

        debugLog('Region aggregated totals', {
            totalRevenue,
            totalContracts,
            totalCustomers,
            totalDeals,
            totalQuotations,
            totalHP
        });

        return {
            branches: branchData,
            summary: {
                totalRevenue,
                totalContracts,
                totalCustomers,
                totalDeals,
                totalQuotations,
                totalHP,
                avgContractValue: totalContracts > 0 ? totalRevenue / totalContracts : 0,
            },
            rawData: {
                contracts,
                deals,
                organizations,
                quotations,
            },
        };
    } catch (error) {
        console.error('Error fetching region data:', error);
        throw error;
    }
}

/**
 * Get Branch Level Data
 */
export async function getBranchData(branchId, filters = {}) {
    try {
        debugLog('getBranchData called', { branchId, filters });

        const contractFilters = { branch: branchId }; // Changed: No docstatus filter
        const quotationFilters = { branch: branchId, docstatus: 1 };
        const dealFilters = { branch: branchId };
        const orgFilters = { branch: branchId };

        if (filters.date) {
            contractFilters.date = filters.date;
            quotationFilters.date = filters.date;
        }

        // Fetch all data for this branch
        const [contracts, deals, organizations, quotations] = await Promise.all([
            fetchFrappeData('CRM Contract', [
                'name', 'customer', 'customer_name', 'region', 'branch',
                'date', 'amount', 'total_usd', 'start_date', 'expiry_date',
                'total_hp', 'currency', 'docstatus', 'industry', 'parent_vertical', 'deal_type', 'owner', "custom_contract_status"
            ], contractFilters),
            fetchFrappeData('CRM Deal', [
                'name', 'customer', 'customer_name', 'region', 'branch',
                'register_date', 'annual_revenue', 'status', 'deal_type',
                'warranty_amc_status', 'owner'
            ], dealFilters),
            fetchFrappeData('CRM Organization', [
                'name', 'organization_name', 'customer_hc', 'region',
                'branch', 'industry', 'parent_vertical', 'customer_type'
            ], orgFilters),
            fetchFrappeData('CRM Quotation', [
                'name', 'customer', 'customer_name', 'region', 'branch',
                'date', 'status', 'amount', 'total_usd', 'total_hp',
                'docstatus', 'owner'
            ], quotationFilters),
        ]);

        debugLog('Branch data fetched', {
            contracts: contracts.length,
            deals: deals.length,
            organizations: organizations.length,
            quotations: quotations.length
        });

        // Aggregate data by manager/owner
        const managerMap = new Map();

        // Get ALL unique owners from deals, contracts, and quotations
        const allOwners = new Set();
        deals.forEach(d => {
            if (d.owner && d.owner !== 'Administrator') allOwners.add(d.owner);
            if (d.deal_owner && d.deal_owner !== 'Administrator') allOwners.add(d.deal_owner);
        });
        contracts.forEach(c => {
            if (c.owner && c.owner !== 'Administrator') allOwners.add(c.owner);
        });
        quotations.forEach(q => {
            if (q.owner && q.owner !== 'Administrator') allOwners.add(q.owner);
        });

        debugLog('Branch owners found', { count: allOwners.size, owners: Array.from(allOwners) });

        // Initialize manager map with all found owners
        allOwners.forEach(owner => {
            managerMap.set(owner, {
                managerId: owner,
                managerName: owner,
                revenue: 0,
                contracts: 0,
                deals: 0,
                customers: new Set(),
                quotations: 0,
                totalHP: 0,
                contractsList: [],
                dealsList: [],
                quotationsList: [],
            });
        });

        // Aggregate contracts by owner
        contracts.forEach(contract => {
            const owner = contract.owner || 'Unassigned';
            if (!managerMap.has(owner)) {
                managerMap.set(owner, {
                    managerId: owner,
                    managerName: owner,
                    revenue: 0,
                    contracts: 0,
                    deals: 0,
                    customers: new Set(),
                    quotations: 0,
                    totalHP: 0,
                    contractsList: [],
                    dealsList: [],
                    quotationsList: [],
                });
            }

            const manager = managerMap.get(owner);
            manager.revenue += parseFloat(contract.amount || 0);
            manager.contracts += 1;
            manager.totalHP += parseFloat(contract.total_hp || 0);
            manager.contractsList.push(contract);
            if (contract.customer) {
                manager.customers.add(contract.customer);
            }
        });

        // Aggregate deals by owner
        deals.forEach(deal => {
            const owner = deal.deal_owner || deal.owner || 'Unassigned';
            if (!managerMap.has(owner) && owner !== 'Administrator') {
                managerMap.set(owner, {
                    managerId: owner,
                    managerName: owner,
                    revenue: 0,
                    contracts: 0,
                    deals: 0,
                    customers: new Set(),
                    quotations: 0,
                    totalHP: 0,
                    contractsList: [],
                    dealsList: [],
                    quotationsList: [],
                });
            }

            if (managerMap.has(owner)) {
                const manager = managerMap.get(owner);
                manager.deals += 1;
                manager.dealsList.push(deal);
            }
        });

        // Aggregate quotations by owner
        quotations.forEach(quote => {
            const owner = quote.owner || 'Unassigned';
            if (managerMap.has(owner)) {
                const manager = managerMap.get(owner);
                manager.quotations += 1;
                manager.quotationsList.push(quote);
            }
        });

        // Convert Set to count for customers
        managerMap.forEach(manager => {
            manager.customers = manager.customers.size;
        });

        // Calculate totals
        const managerData = Array.from(managerMap.values());
        const totalRevenue = contracts.reduce((sum, c) => sum + parseFloat(c.amount || 0), 0);
        const totalContracts = contracts.length;
        const totalCustomers = organizations.length;
        const totalDeals = deals.length;
        const totalQuotations = quotations.length;
        const totalHP = contracts.reduce((sum, c) => sum + parseFloat(c.total_hp || 0), 0);

        debugLog('Branch aggregated totals', {
            totalRevenue,
            totalContracts,
            totalCustomers,
            totalDeals,
            totalQuotations,
            totalHP
        });

        return {
            managers: managerData,
            summary: {
                totalRevenue,
                totalContracts,
                totalCustomers,
                totalDeals,
                totalQuotations,
                totalHP,
                avgContractValue: totalContracts > 0 ? totalRevenue / totalContracts : 0,
            },
            rawData: {
                contracts,
                deals,
                organizations,
                quotations,
            },
        };
    } catch (error) {
        console.error('Error fetching branch data:', error);
        throw error;
    }
}

/**
 * Format currency value
 */
export function formatCurrency(value) {
    if (value >= 10000000) {
        return `₹${(value / 10000000).toFixed(2)}Cr`;
    } else if (value >= 100000) {
        return `₹${(value / 100000).toFixed(2)}L`;
    } else {
        return `₹${value.toFixed(2)}`;
    }
}

/**
 * Format HP value
 */
export function formatHP(value) {
    return `${value.toLocaleString()} HP`;
}