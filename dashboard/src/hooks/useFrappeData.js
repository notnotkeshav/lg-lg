// src/hooks/useFrappeData.js
import { useFrappeGetDocList } from 'frappe-react-sdk';
import { useMemo } from 'react';

const REGION_GROUPS = {
    "NORTH": ["NORTH", "NORTH-1", "NORTH-2"],
    "EAST":  ["EAST",  "EAST-1",  "EAST-2"],
};

const REGION_HIERARCHY = {
    'EAST':  ['EAST-1',  'EAST-2'],
    'NORTH': ['NORTH-1', 'NORTH-2'],
};

// ─── filter helpers ───────────────────────────────────────────────────────────

function toArray(v) {
    if (!v) return [];
    if (Array.isArray(v)) return v;
    return [v];
}

function matchesFilter(fieldValue, filterArray) {
    if (!filterArray || filterArray.length === 0) return true;
    return filterArray.includes(fieldValue);
}

function filterByContractStatus(contracts, contractStatus) {
    const statuses = toArray(contractStatus);
    if (statuses.length === 0) return contracts.filter(c => c.custom_contract_status === 'Active');
    if (statuses.includes('Total')) return contracts;
    if (statuses.includes('Active') && statuses.includes('Expired')) return contracts;
    return contracts.filter(c => statuses.includes(c.custom_contract_status));
}

export function contractStatusLabel(contractStatus) {
    const statuses = toArray(contractStatus);
    if (statuses.length === 0 || (statuses.length === 1 && statuses[0] === 'Active')) return 'Active Contracts';
    if (statuses.includes('Total') || (statuses.includes('Active') && statuses.includes('Expired'))) return 'Total Contracts';
    if (statuses.length === 1 && statuses[0] === 'Expired') return 'Expired Contracts';
    return 'Contracts';
}

// ─── useCountryData ───────────────────────────────────────────────────────────

export function useCountryData(filters = {}) {
    const contractFilters = [];
    const contractOrFilters = [];
    const quotationFilters  = [['docstatus', '=', 1]];
    const quotationOrFilters = [];

    if (filters.startDate && filters.endDate) {
        if (filters.usePoDate) {
            quotationOrFilters.push(
                ['start_date_as_per_po', 'between', [filters.startDate, filters.endDate]],
                ['end_date_as_per_po',   'between', [filters.startDate, filters.endDate]]
            );
        } else {
            contractOrFilters.push(
                ['start_date',  'between', [filters.startDate, filters.endDate]],
                ['expiry_date', 'between', [filters.startDate, filters.endDate]]
            );
        }
    }

    if (filters.useCustomerPoDate && filters.customerPoStartDate && filters.customerPoEndDate) {
        contractFilters.push(['customer_po_date', 'between',
            [filters.customerPoStartDate, filters.customerPoEndDate]]);
    }

    const { data: contracts, error: contractsError, isLoading: contractsLoading } = useFrappeGetDocList('CRM Contract', {
        fields: ['name','customer','customer_name','region','branch','date','amount','total_usd',
                 'start_date','expiry_date','total_hp','currency','docstatus','industry',
                 'parent_vertical','deal_type','custom_contract_status','customer_po_date'],
        filters:   contractFilters.length  ? contractFilters  : undefined,
        orFilters: contractOrFilters.length ? contractOrFilters : undefined,
        limit: 0,
    });

    const { data: deals, error: dealsError, isLoading: dealsLoading } = useFrappeGetDocList('CRM Deal', {
        fields: ['name','customer','customer_name','region','branch','register_date',
                 'annual_revenue','status','deal_type','warranty_amc_status','owner','industry','parent_vertical'],
        limit: 0,
    });

    const { data: organizations, error: orgsError, isLoading: orgsLoading } = useFrappeGetDocList('CRM Organization', {
        fields: ['name','organization_name','customer_hc','region','branch','industry','parent_vertical','customer_type'],
        limit: 0,
    });

    const { data: quotations, error: quotationsError, isLoading: quotationsLoading } = useFrappeGetDocList('CRM Quotation', {
        fields: ['name','customer','customer_name','region','branch','date','status','amount','total_usd','total_hp','docstatus'],
        filters: quotationFilters,
        orFilters: quotationOrFilters.length ? quotationOrFilters : undefined,
        limit: 0,
    });

    const { data: regions, error: regionsError, isLoading: regionsLoading } = useFrappeGetDocList('Region Master', {
        fields: ['name','region_name','region_head','region_head_name'],
        limit: 0,
    });

    const isLoading = contractsLoading || dealsLoading || orgsLoading || quotationsLoading || regionsLoading;
    const error     = contractsError   || dealsError   || orgsError   || quotationsError   || regionsError;

    const processedData = useMemo(() => {
        if (!contracts || !deals || !organizations || !quotations || !regions) return null;

        let filteredContracts = contracts;
        let filteredDeals     = deals;
        let filteredOrgs      = organizations;

        const verticals = toArray(filters.vertical);
        const dealTypes = toArray(filters.dealType);
        const statuses  = toArray(filters.status);

        if (verticals.length > 0) {
            filteredContracts = filteredContracts.filter(c => matchesFilter(c.parent_vertical, verticals));
            filteredOrgs      = filteredOrgs.filter(o => matchesFilter(o.parent_vertical, verticals));
        }
        if (dealTypes.length > 0) {
            filteredContracts = filteredContracts.filter(c => matchesFilter(c.deal_type, dealTypes));
            filteredDeals     = filteredDeals.filter(d => matchesFilter(d.deal_type, dealTypes));
        }
        if (statuses.length > 0) {
            filteredDeals = filteredDeals.filter(d => matchesFilter(d.status, statuses));
        }

        filteredContracts = filterByContractStatus(filteredContracts, filters.contractStatus);

        const regionMap = new Map();
        regions.forEach(region => {
            if (region.name === 'EAST' || region.name === 'NORTH') return;
            regionMap.set(region.name, {
                regionId: region.name, regionName: region.region_name,
                regionHead: region.region_head_name || region.region_head,
                revenue: 0, contracts: 0, deals: 0,
                amcRenewal: 0, warrantyConversion: 0, lostAmcConversion: 0, lostWarrantyConversion: 0,
                customers: new Set(), quotations: 0, totalHP: 0,
                isParent: false, parentRegionId: null,
            });
        });

        Object.entries(REGION_HIERARCHY).forEach(([parentId, childIds]) => {
            childIds.forEach(childId => {
                if (regionMap.has(childId)) regionMap.get(childId).parentRegionId = parentId;
            });
            regionMap.set(parentId, {
                regionId: parentId, regionName: parentId, regionHead: 'Multiple',
                revenue: 0, contracts: 0, deals: 0,
                amcRenewal: 0, warrantyConversion: 0, lostAmcConversion: 0, lostWarrantyConversion: 0,
                customers: new Set(), quotations: 0, totalHP: 0,
                isParent: true, parentRegionId: null, subRegions: childIds,
            });
        });

        filteredContracts.forEach(contract => {
            if (contract.region === 'EAST' || contract.region === 'NORTH') return;
            if (!contract.region || !regionMap.has(contract.region)) return;
            const region = regionMap.get(contract.region);
            const amount = parseFloat(contract.amount || 0);
            const type   = (contract.deal_type || '').toLowerCase().trim();
            region.revenue += amount; region.contracts += 1;
            region.totalHP += parseFloat(contract.total_hp || 0);
            if (contract.customer) region.customers.add(contract.customer);
            if (type === 'amc renewal') region.amcRenewal++;
            else if (type === 'warranty conversion' || type === 'warranty amc conversion') region.warrantyConversion++;
            else if (type === 'lost amc conversion') region.lostAmcConversion++;
            else if (type === 'lost warranty conversion') region.lostWarrantyConversion++;
            if (region.parentRegionId && regionMap.has(region.parentRegionId)) {
                const parent = regionMap.get(region.parentRegionId);
                parent.revenue += amount; parent.contracts += 1;
                parent.totalHP += parseFloat(contract.total_hp || 0);
                if (contract.customer) parent.customers.add(contract.customer);
                if (type === 'amc renewal') parent.amcRenewal++;
                else if (type === 'warranty conversion' || type === 'warranty amc conversion') parent.warrantyConversion++;
                else if (type === 'lost amc conversion') parent.lostAmcConversion++;
                else if (type === 'lost warranty conversion') parent.lostWarrantyConversion++;
            }
        });

        filteredDeals.forEach(deal => {
            if (deal.region === 'EAST' || deal.region === 'NORTH') return;
            if (!deal.region || !regionMap.has(deal.region)) return;
            regionMap.get(deal.region).deals += 1;
            const region = regionMap.get(deal.region);
            if (region.parentRegionId && regionMap.has(region.parentRegionId))
                regionMap.get(region.parentRegionId).deals += 1;
        });

        quotations.forEach(quote => {
            if (quote.region === 'EAST' || quote.region === 'NORTH') return;
            if (!quote.region || !regionMap.has(quote.region)) return;
            regionMap.get(quote.region).quotations += 1;
            const region = regionMap.get(quote.region);
            if (region.parentRegionId && regionMap.has(region.parentRegionId))
                regionMap.get(region.parentRegionId).quotations += 1;
        });

        regionMap.forEach(r => { r.customers = r.customers.size; });

        const regionData     = Array.from(regionMap.values());
        const totalRevenue   = filteredContracts.reduce((s, c) => s + parseFloat(c.amount   || 0), 0);
        const totalContracts = filteredContracts.length;
        const totalHP        = filteredContracts.reduce((s, c) => s + parseFloat(c.total_hp || 0), 0);

        return {
            regions: regionData,
            summary: {
                totalRevenue, totalContracts, totalContractsAll: contracts.length,
                totalCustomers: filteredOrgs.length, totalDeals: filteredDeals.length,
                totalQuotations: quotations.length, totalHP,
                avgContractValue: totalContracts > 0 ? totalRevenue / totalContracts : 0,
            },
            rawData: { contracts: filteredContracts, deals: filteredDeals, organizations: filteredOrgs, quotations },
        };
    }, [contracts, deals, organizations, quotations, regions, filters]);

    return { data: processedData, isLoading, error };
}

// ─── useRegionData ────────────────────────────────────────────────────────────

export function useRegionData(regionId, filters = {}) {
    const regionFilterValue  = REGION_GROUPS[regionId] || [regionId];
    const contractFilters    = [['region', 'in', regionFilterValue]];
    const dealFilters        = [['region', 'in', regionFilterValue]];
    const orgFilters         = [['region', 'in', regionFilterValue]];
    const quotationFilters   = [['region', 'in', regionFilterValue], ['docstatus', '=', 1]];
    const contractOrFilters  = [];
    const quotationOrFilters = [];

    if (filters.startDate && filters.endDate) {
        if (filters.usePoDate) {
            quotationOrFilters.push(
                ['start_date_as_per_po', 'between', [filters.startDate, filters.endDate]],
                ['end_date_as_per_po',   'between', [filters.startDate, filters.endDate]]
            );
        } else {
            contractOrFilters.push(
                ['start_date',  'between', [filters.startDate, filters.endDate]],
                ['expiry_date', 'between', [filters.startDate, filters.endDate]]
            );
        }
    }

    if (filters.useCustomerPoDate && filters.customerPoStartDate && filters.customerPoEndDate) {
        contractFilters.push(['customer_po_date', 'between',
            [filters.customerPoStartDate, filters.customerPoEndDate]]);
    }

    const { data: contracts, error: contractsError, isLoading: contractsLoading } = useFrappeGetDocList('CRM Contract', {
        fields: ['name','customer','customer_name','region','branch','date','amount','total_usd',
                 'start_date','expiry_date','total_hp','currency','docstatus','industry',
                 'parent_vertical','deal_type','custom_contract_status','customer_po_date'],
        filters: contractFilters, orFilters: contractOrFilters.length ? contractOrFilters : undefined, limit: 0,
    });

    const { data: deals, error: dealsError, isLoading: dealsLoading } = useFrappeGetDocList('CRM Deal', {
        fields: ['name','customer','customer_name','region','branch','register_date','annual_revenue','status','deal_type','warranty_amc_status','owner'],
        filters: dealFilters, limit: 0,
    });

    const { data: organizations, error: orgsError, isLoading: orgsLoading } = useFrappeGetDocList('CRM Organization', {
        fields: ['name','organization_name','customer_hc','region','branch','industry','parent_vertical','customer_type'],
        filters: orgFilters, limit: 0,
    });

    const { data: quotations, error: quotationsError, isLoading: quotationsLoading } = useFrappeGetDocList('CRM Quotation', {
        fields: ['name','customer','customer_name','region','branch','date','status','amount','total_usd','total_hp','docstatus'],
        filters: quotationFilters, orFilters: quotationOrFilters.length ? quotationOrFilters : undefined, limit: 0,
    });

    const { data: branches, error: branchesError, isLoading: branchesLoading } = useFrappeGetDocList('Region Branches', {
        fields: ['name','branch_id','branch_name','branch_head','branch_head_name','region'],
        filters: [['region', 'in', regionFilterValue]], limit: 0,
    });

    const isLoading = contractsLoading || dealsLoading || orgsLoading || quotationsLoading || branchesLoading;
    const error     = contractsError   || dealsError   || orgsError   || quotationsError   || branchesError;

    const processedData = useMemo(() => {
        if (!contracts || !deals || !organizations || !quotations || !branches) return null;

        let filteredContracts = contracts;
        let filteredDeals     = deals;
        let filteredOrgs      = organizations;

        const verticals    = toArray(filters.vertical);
        const dealTypes    = toArray(filters.dealType);
        const statuses     = toArray(filters.status);
        const branchFilter = toArray(filters.branch);

        if (verticals.length > 0) {
            filteredContracts = filteredContracts.filter(c => matchesFilter(c.parent_vertical, verticals));
            filteredOrgs      = filteredOrgs.filter(o => matchesFilter(o.parent_vertical, verticals));
        }
        if (dealTypes.length > 0) {
            filteredContracts = filteredContracts.filter(c => matchesFilter(c.deal_type, dealTypes));
            filteredDeals     = filteredDeals.filter(d => matchesFilter(d.deal_type, dealTypes));
        }
        if (statuses.length > 0) {
            filteredDeals = filteredDeals.filter(d => matchesFilter(d.status, statuses));
        }

        filteredContracts = filterByContractStatus(filteredContracts, filters.contractStatus);

        if (branchFilter.length > 0) {
            filteredContracts = filteredContracts.filter(c => branchFilter.includes(c.branch));
        }

        const branchMap = new Map();
        branches.forEach(branch => {
            branchMap.set(branch.name, {
                branchId: branch.name, branchName: branch.branch_name,
                branchHead: branch.branch_head_name || branch.branch_head,
                revenue: 0, contracts: 0, deals: 0,
                customers: new Set(), quotations: 0, totalHP: 0,
            });
        });

        filteredContracts.forEach(contract => {
            if (contract.branch && branchMap.has(contract.branch)) {
                const branch = branchMap.get(contract.branch);
                branch.revenue   += parseFloat(contract.amount   || 0);
                branch.contracts += 1;
                branch.totalHP   += parseFloat(contract.total_hp || 0);
                if (contract.customer) branch.customers.add(contract.customer);
            }
        });

        filteredDeals.forEach(deal => {
            if (deal.branch && branchMap.has(deal.branch)) branchMap.get(deal.branch).deals += 1;
        });
        quotations.forEach(quote => {
            if (quote.branch && branchMap.has(quote.branch)) branchMap.get(quote.branch).quotations += 1;
        });

        branchMap.forEach(b => { b.customers = b.customers.size; });

        const branchData     = Array.from(branchMap.values());
        const totalRevenue   = filteredContracts.reduce((s, c) => s + parseFloat(c.amount   || 0), 0);
        const totalContracts = filteredContracts.length;
        const totalHP        = filteredContracts.reduce((s, c) => s + parseFloat(c.total_hp || 0), 0);

        return {
            branches: branchData,
            summary: {
                totalRevenue, totalContracts, totalContractsAll: contracts.length,
                totalCustomers: filteredOrgs.length, totalDeals: filteredDeals.length,
                totalQuotations: quotations.length, totalHP,
                avgContractValue: totalContracts > 0 ? totalRevenue / totalContracts : 0,
            },
            rawData: { contracts: filteredContracts, deals: filteredDeals, organizations: filteredOrgs, quotations },
        };
    }, [contracts, deals, organizations, quotations, branches, filters]);

    return { data: processedData, isLoading, error };
}

// ─── useBranchData ────────────────────────────────────────────────────────────

export function useBranchData(branchId, filters = {}) {
    const contractFilters    = [['branch', '=', branchId]];
    const quotationFilters   = [['branch', '=', branchId], ['docstatus', '=', 1]];
    const dealFilters        = [['branch', '=', branchId]];
    const orgFilters         = [['branch', '=', branchId]];
    const contractOrFilters  = [];
    const quotationOrFilters = [];

    if (filters.startDate && filters.endDate) {
        if (filters.usePoDate) {
            quotationOrFilters.push(
                ['start_date_as_per_po', 'between', [filters.startDate, filters.endDate]],
                ['end_date_as_per_po',   'between', [filters.startDate, filters.endDate]]
            );
        } else {
            contractOrFilters.push(
                ['start_date',  'between', [filters.startDate, filters.endDate]],
                ['expiry_date', 'between', [filters.startDate, filters.endDate]]
            );
        }
    }

    if (filters.useCustomerPoDate && filters.customerPoStartDate && filters.customerPoEndDate) {
        contractFilters.push(['customer_po_date', 'between',
            [filters.customerPoStartDate, filters.customerPoEndDate]]);
    }

    const { data: branchInfo, error: branchInfoError, isLoading: branchInfoLoading } = useFrappeGetDocList('Region Branches', {
        fields: ['name','branch_id','branch_name','branch_head','branch_head_name','region'],
        filters: [['name', '=', branchId]], limit: 1,
    });

    const { data: contracts, error: contractsError, isLoading: contractsLoading } = useFrappeGetDocList('CRM Contract', {
        fields: ['name','customer','customer_name','region','branch','date','amount',
                 'start_date','expiry_date','total_hp','currency','docstatus',
                 'industry','parent_vertical','deal_type','owner','custom_contract_status','customer_po_date'],
        filters: contractFilters, orFilters: contractOrFilters.length ? contractOrFilters : undefined, limit: 0,
    });

    const { data: deals, error: dealsError, isLoading: dealsLoading } = useFrappeGetDocList('CRM Deal', {
        fields: ['name','customer','customer_name','region','branch','register_date','annual_revenue','status','deal_type','warranty_amc_status','owner'],
        filters: dealFilters, limit: 0,
    });

    const { data: organizations, error: orgsError, isLoading: orgsLoading } = useFrappeGetDocList('CRM Organization', {
        fields: ['name','organization_name','customer_hc','region','branch','industry','parent_vertical','customer_type'],
        filters: orgFilters, limit: 0,
    });

    const { data: quotations, error: quotationsError, isLoading: quotationsLoading } = useFrappeGetDocList('CRM Quotation', {
        fields: ['name','customer','customer_name','region','branch','date','status','amount','total_hp','docstatus','owner'],
        filters: quotationFilters, orFilters: quotationOrFilters.length ? quotationOrFilters : undefined, limit: 0,
    });

    const isLoading = contractsLoading || dealsLoading || orgsLoading || quotationsLoading || branchInfoLoading;
    const error     = contractsError   || dealsError   || orgsError   || quotationsError   || branchInfoError;

    const processedData = useMemo(() => {
        if (!contracts || !deals || !organizations || !quotations || !branchInfo?.length) return null;

        const currentBranch  = branchInfo[0];
        const branchHeadId   = currentBranch.branch_head_name || currentBranch.branch_head || 'Unassigned';
        const branchHeadName = currentBranch.branch_head_name || currentBranch.branch_head || 'Unassigned';

        let filteredContracts  = contracts;
        let filteredDeals      = deals;
        let filteredOrgs       = organizations;
        let filteredQuotations = quotations;

        const verticals = toArray(filters.vertical);
        const dealTypes = toArray(filters.dealType);
        const statuses  = toArray(filters.status);

        if (verticals.length > 0) {
            filteredContracts = filteredContracts.filter(c => matchesFilter(c.parent_vertical, verticals));
            filteredOrgs      = filteredOrgs.filter(o => matchesFilter(o.parent_vertical, verticals));
        }
        if (dealTypes.length > 0) {
            filteredContracts = filteredContracts.filter(c => matchesFilter(c.deal_type, dealTypes));
            filteredDeals     = filteredDeals.filter(d => matchesFilter(d.deal_type, dealTypes));
        }
        if (statuses.length > 0) {
            filteredDeals = filteredDeals.filter(d => matchesFilter(d.status, statuses));
        }

        filteredContracts = filterByContractStatus(filteredContracts, filters.contractStatus);

        const customers = new Set();
        let revenue = 0, contractsCount = 0, dealsCount = 0, quotationsCount = 0, totalHP = 0;
        filteredContracts.forEach(c => {
            revenue += parseFloat(c.amount || 0); contractsCount += 1;
            totalHP += parseFloat(c.total_hp || 0);
            if (c.customer) customers.add(c.customer);
        });
        filteredDeals.forEach(()      => dealsCount++);
        filteredQuotations.forEach(() => quotationsCount++);

        const managerData = [{
            managerId: branchHeadId, managerName: branchHeadName,
            revenue, contracts: contractsCount, deals: dealsCount,
            quotations: quotationsCount, customers: customers.size, totalHP,
            contractsList: filteredContracts, dealsList: filteredDeals, quotationsList: filteredQuotations,
        }];

        return {
            managers: managerData,
            branchInfo: { ...currentBranch, branch_head_id: branchHeadId, branch_head_email: currentBranch.branch_head },
            summary: {
                totalRevenue: revenue, totalContracts: contractsCount, totalContractsAll: contracts.length,
                totalCustomers: filteredOrgs.length, totalDeals: dealsCount,
                totalQuotations: quotationsCount, totalHP,
                avgContractValue: contractsCount > 0 ? revenue / contractsCount : 0,
            },
            rawData: { contracts: filteredContracts, deals: filteredDeals, organizations: filteredOrgs, quotations: filteredQuotations },
        };
    }, [contracts, deals, organizations, quotations, branchInfo, filters]);

    return { data: processedData, isLoading, error };
}

// ─── helpers ──────────────────────────────────────────────────────────────────

export function formatCurrency(value) {
    if (value >= 10000000) return `\u20b9${(value / 10000000).toFixed(2)}Cr`;
    if (value >= 100000)   return `\u20b9${(value / 100000).toFixed(2)}L`;
    return `\u20b9${value.toFixed(2)}`;
}

export function formatHP(value) {
    return `${value.toLocaleString()} HP`;
}