// src/pages/Manager.jsx
import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { IndianRupee, FileText, Users, Target, X } from 'lucide-react';
import { useRegionData, formatCurrency } from '../hooks/useFrappeData';
import { useFilters } from '../contexts/FilterContext';
import { COLORS } from '../constants/theme';
import { filterContractsLastNMonths, createContractTimeline } from '../utils/dateUtils';
import KPICard from '../components/common/KPICard';
import FilterPanel from '../components/common/FilterPanel';
import StackedBarChart, { formatCurrencyCompact, formatNumberCompact } from '../components/charts/StackedBarChart';
import DonutChart from '../components/charts/DonutChart';
import PieChart from '../components/charts/PieChart';
import AreaChart from '../components/charts/AreaChart';
import Breadcrumb from '../components/common/BreadCrumb';
import DataTable from '../components/common/DataTable3';

export default function Manager() {
    const { managerId } = useParams();
    const navigate = useNavigate();
    const location = useLocation();
    const { globalFilters, updateFilters, resetFilters } = useFilters();

    const [localFilters, setLocalFilters] = useState(globalFilters);
    const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
    const [showIndustryModal, setShowIndustryModal] = useState(false);
    const [selectedVerticalData, setSelectedVerticalData] = useState(null);

    const regionId = location.state?.regionId || 'EAST-1';
    const managerName = location.state?.managerName || managerId;
    const branchHeadId = location.state?.branchHeadId || managerId;

    useEffect(() => {
        setLocalFilters(globalFilters);
    }, [globalFilters]);

    const { data: regionData, isLoading, error } = useRegionData(regionId, {
        startDate: globalFilters.startDate,
        endDate: globalFilters.endDate,
        industry: globalFilters.industry,
        vertical: globalFilters.vertical,
        dealType: globalFilters.dealType,
        status: globalFilters.status,
        contractStatus: globalFilters.contractStatus,
        useCustomerPoDate: globalFilters.useCustomerPoDate,
        customerPoStartDate: globalFilters.customerPoStartDate,
        customerPoEndDate: globalFilters.customerPoEndDate,
    });

    const handleApplyFilters = () => {
        updateFilters(localFilters);
    };

    const handleResetFilters = () => {
        setLocalFilters({});
        resetFilters();
    };

    const handleBranchClick = (branchId) => {
        navigate(`/branch/${branchId}`);
    };

    const handleSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });
    };

    const handleVerticalClick = (segment) => {
        if (chartData && chartData.industryByVertical) {
            const industryData = chartData.industryByVertical[segment.name];
            setSelectedVerticalData({
                verticalName: segment.name,
                totalRevenue: segment.value,
                industries: industryData || []
            });
            setShowIndustryModal(true);
        }
    };

    const managerData = useMemo(() => {
        if (!regionData) return null;

        const allBranches = regionData.branches || [];

        const managedBranchObjs = allBranches.filter(b => {
            const head = b.branchHead || '';
            return head === branchHeadId || head === managerId || head === managerName;
        });

        const managedBranchIds = managedBranchObjs.map(b => b.branchId);
        const managedBranchSet = new Set(managedBranchIds);

        const allContracts      = regionData.rawData?.contracts      || [];
        const allDeals          = regionData.rawData?.deals           || [];
        const allQuotations     = regionData.rawData?.quotations      || [];
        const allOrganizations  = regionData.rawData?.organizations   || [];

        // Contracts already status-filtered by useRegionData; just scope to this manager's branches
        let managerContracts      = allContracts.filter(c => managedBranchSet.has(c.branch));
        let managerDeals          = allDeals.filter(d => managedBranchSet.has(d.branch));
        let managerQuotations     = allQuotations.filter(q => managedBranchSet.has(q.branch));
        let managerOrganizations  = allOrganizations.filter(o => managedBranchSet.has(o.branch));

        if (globalFilters.branch && globalFilters.branch !== 'all') {
            managerContracts     = managerContracts.filter(c => c.branch === globalFilters.branch);
            managerDeals         = managerDeals.filter(d => d.branch === globalFilters.branch);
            managerQuotations    = managerQuotations.filter(q => q.branch === globalFilters.branch);
            managerOrganizations = managerOrganizations.filter(o => o.branch === globalFilters.branch);
        }

        const customerSet = new Set();
        managerContracts.forEach(c => { if (c.customer) customerSet.add(c.customer); });

        const totalRevenue   = managerContracts.reduce((sum, c) => sum + parseFloat(c.amount || 0), 0);
        const totalContracts = managerContracts.length;

        // totalContractsAll: same branch scope but no contractStatus filter — for KPI subtitle.
        // regionData.rawData.contracts is already status-filtered by the hook, so we need the
        // unfiltered count. Approximate via the branches aggregate which always counts all statuses.
        const totalContractsAll = managedBranchObjs.reduce((sum, b) => sum + (b.contracts || 0), 0);

        return {
            summary: {
                totalRevenue,
                totalContracts,
                totalContractsAll,
                totalCustomers: customerSet.size,
                totalDeals: managerDeals.length,
                totalQuotations: managerQuotations.length,
                totalBranches: managedBranchIds.length,
                avgContractValue: totalContracts > 0 ? totalRevenue / totalContracts : 0,
            },
            rawData: {
                contracts: managerContracts,
                deals: managerDeals,
                quotations: managerQuotations,
                organizations: managerOrganizations,
                branches: managedBranchIds,
            },
            branchDetails: managedBranchObjs,
        };
    }, [regionData, managerId, branchHeadId, managerName, globalFilters.branch]);

    const CONTRACT_STATUS_LABEL = {
        Active:  'Active Contracts',
        Expired: 'Expired Contracts',
        Total:   'Total Contracts',
    };
    const contractKpiTitle =
        CONTRACT_STATUS_LABEL[globalFilters.contractStatus] ?? 'Active Contracts';

    const chartData = useMemo(() => {
        if (!managerData) return null;

        const { rawData, branchDetails } = managerData;
        const useCustomerPoDate = globalFilters.useCustomerPoDate || false;

        const filteredContracts = filterContractsLastNMonths(rawData.contracts, 12, useCustomerPoDate);

        const categorizeDealType = (dealType) => {
            const type = (dealType || '').toLowerCase().trim();
            if (type === 'amc renewal') return 'amcRenewal';
            if (type === 'warranty conversion' || type === 'warranty amc conversion') return 'warrantyConversion';
            if (type === 'lost amc conversion') return 'lostAmcConversion';
            if (type === 'lost warranty conversion') return 'lostWarrantyConversion';
        };

        const revenueByVertical = () => {
            const map = new Map();
            filteredContracts.forEach(c => {
                const v = c.parent_vertical || 'Uncategorized';
                map.set(v, (map.get(v) || 0) + parseFloat(c.amount || 0));
            });
            return Array.from(map, ([name, value]) => ({ name, value }));
        };

        const industryByVertical = () => {
            const verticalMap = new Map();
            filteredContracts.forEach(c => {
                const vertical = c.parent_vertical || 'Uncategorized';
                const industry = c.industry || 'Unknown';
                if (!verticalMap.has(vertical)) verticalMap.set(vertical, new Map());
                const industryMap = verticalMap.get(vertical);
                industryMap.set(industry, (industryMap.get(industry) || 0) + parseFloat(c.amount || 0));
            });
            const result = {};
            verticalMap.forEach((industryMap, vertical) => {
                result[vertical] = Array.from(industryMap, ([name, value]) => ({ name, value }));
            });
            return result;
        };

        const dealStatus = () => {
            const map = new Map();
            rawData.deals.forEach(d => {
                const s = d.status || 'Unknown';
                map.set(s, (map.get(s) || 0) + 1);
            });
            return Array.from(map, ([name, value]) => ({ name, value }));
        };

        const contractTimelineData = createContractTimeline(filteredContracts, 12, useCustomerPoDate);

        const revenueByBranchStacked = branchDetails.map(b => ({
            name: b.branchName, branchId: b.branchId,
            amcRenewal: 0, warrantyConversion: 0, lostAmcConversion: 0, lostWarrantyConversion: 0,
        }));
        filteredContracts.forEach(c => {
            const branch = revenueByBranchStacked.find(b => b.branchId === c.branch);
            if (branch) {
                const amount   = parseFloat(c.amount || 0);
                const category = categorizeDealType(c.deal_type);
                if (category) branch[category] += amount;
            }
        });

        const contractsByBranchStacked = branchDetails.map(b => ({
            name: b.branchName, branchId: b.branchId,
            amcRenewal: 0, warrantyConversion: 0, lostAmcConversion: 0, lostWarrantyConversion: 0,
        }));
        filteredContracts.forEach(c => {
            const branch   = contractsByBranchStacked.find(b => b.branchId === c.branch);
            const category = categorizeDealType(c.deal_type);
            if (branch && category) branch[category] += 1;
        });

        return {
            revenueByVertical: revenueByVertical(),
            industryByVertical: industryByVertical(),
            dealStatus: dealStatus(),
            contractTimeline: contractTimelineData,
            revenueByBranchStacked,
            contractsByBranchStacked,
        };
    }, [managerData, globalFilters.useCustomerPoDate]);

    const sortedBranches = useMemo(() => {
        if (!managerData) return [];

        const branchMap = new Map();
        managerData.branchDetails.forEach(b => {
            branchMap.set(b.branchId, {
                branchId: b.branchId, branchName: b.branchName, branchHead: b.branchHead,
                revenue: 0, contracts: 0, deals: 0, customers: 0,
                amcRenewal: 0, warrantyConversion: 0, lostAmcConversion: 0, lostWarrantyConversion: 0,
            });
        });

        managerData.rawData.contracts.forEach(c => {
            if (c.branch && branchMap.has(c.branch)) {
                const branch = branchMap.get(c.branch);
                branch.revenue    += parseFloat(c.amount || 0);
                branch.contracts  += 1;
                const type = (c.deal_type || '').toLowerCase().trim();
                if      (type === 'amc renewal')                                         branch.amcRenewal++;
                else if (type === 'warranty conversion' || type === 'warranty amc conversion') branch.warrantyConversion++;
                else if (type === 'lost amc conversion')                                 branch.lostAmcConversion++;
                else if (type === 'lost warranty conversion')                            branch.lostWarrantyConversion++;
            }
        });

        managerData.rawData.deals.forEach(d => {
            if (d.branch && branchMap.has(d.branch)) branchMap.get(d.branch).deals++;
        });

        managerData.rawData.organizations.forEach(o => {
            if (o.branch && branchMap.has(o.branch)) branchMap.get(o.branch).customers++;
        });

        let result = Array.from(branchMap.values());
        if (sortConfig.key) {
            result.sort((a, b) => {
                if (a[sortConfig.key] < b[sortConfig.key]) return sortConfig.direction === 'asc' ? -1 : 1;
                if (a[sortConfig.key] > b[sortConfig.key]) return sortConfig.direction === 'asc' ? 1 : -1;
                return 0;
            });
        }
        return result;
    }, [managerData, sortConfig]);

    const sortedContracts = useMemo(() => {
        if (!managerData) return [];
        let result = [...managerData.rawData.contracts];
        if (sortConfig.key) {
            result.sort((a, b) => {
                let aVal = a[sortConfig.key];
                let bVal = b[sortConfig.key];
                if (sortConfig.key === 'amount') {
                    aVal = parseFloat(aVal || 0);
                    bVal = parseFloat(bVal || 0);
                }
                if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
                if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
                return 0;
            });
        }
        return result;
    }, [managerData, sortConfig]);

    const branchColumns = [
        { key: 'branchName',           label: 'Branch',               bold: true },
        { key: 'revenue',              label: 'Revenue',              align: 'right', render: v => formatCurrency(v) },
        { key: 'contracts',            label: 'Total Contracts',      align: 'right' },
        { key: 'amcRenewal',           label: 'AMC Renewal',          align: 'right' },
        { key: 'warrantyConversion',   label: 'Warranty Conv.',       align: 'right' },
        { key: 'lostAmcConversion',    label: 'Lost AMC Conv.',       align: 'right' },
        { key: 'lostWarrantyConversion', label: 'Lost Warranty Conv.', align: 'right' },
    ];

    const contractColumns = [
        { key: 'name',                   label: 'Contract ID', bold: true },
        { key: 'customer_name',          label: 'Customer' },
        { key: 'branch',                 label: 'Branch' },
        { key: 'date',                   label: 'Date' },
        { key: 'amount',                 label: 'Amount', align: 'right', render: v => formatCurrency(v) },
        { key: 'deal_type',              label: 'Deal Type' },
        { key: 'custom_contract_status', label: 'Status' },
    ];

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-xl font-semibold" style={{ color: COLORS.text.secondary }}>
                    Loading manager data...
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="bg-white rounded-lg shadow-md p-6 max-w-md">
                    <h3 className="text-xl font-semibold text-red-600 mb-2">Error Loading Manager</h3>
                    <p className="text-gray-600">{error.message}</p>
                </div>
            </div>
        );
    }

    if (!managerData) return null;

    return (
        <div className="min-h-screen" style={{ backgroundColor: COLORS.background }}>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                <div className="mb-6">
                    <Breadcrumb
                        items={[
                            { label: regionId, href: `/region/${regionId}` },
                            { label: managerName }
                        ]}
                    />
                    <h1 className="text-3xl font-bold" style={{ color: COLORS.text.primary }}>
                        Area Manager Dashboard
                    </h1>
                    <p className="text-gray-600 mt-1">{managerName} - {regionId}</p>
                </div>

                <FilterPanel
                    filters={localFilters}
                    setFilters={setLocalFilters}
                    onApply={handleApplyFilters}
                    onReset={handleResetFilters}
                    additionalOptions={{
                        branches: managerData.branchDetails.map(b => ({
                            value: b.branchId,
                            label: b.branchName,
                        }))
                    }}
                />

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
                    <KPICard
                        title="Total Revenue"
                        value={formatCurrency(managerData.summary.totalRevenue)}
                        subtitle={`Avg: ${formatCurrency(managerData.summary.avgContractValue)}`}
                        icon={IndianRupee}
                    />
                    <KPICard
                        title={contractKpiTitle}
                        value={managerData.summary.totalContracts.toLocaleString()}
                        subtitle={`All statuses: ${managerData.summary.totalContractsAll.toLocaleString()}`}
                        icon={FileText}
                    />
                    <KPICard
                        title="Total Customers"
                        value={managerData.summary.totalCustomers.toLocaleString()}
                        icon={Users}
                    />
                    <KPICard
                        title="Active Opportunities"
                        value={managerData.summary.totalDeals.toLocaleString()}
                        subtitle={`Branches: ${managerData.summary.totalBranches}`}
                        icon={Target}
                    />
                </div>

                {chartData && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <StackedBarChart
                            data={chartData.revenueByBranchStacked}
                            title="Revenue by Branch"
                            stacks={[
                                { dataKey: 'amcRenewal',           name: 'AMC Renewal',           color: '#10b981' },
                                { dataKey: 'warrantyConversion',   name: 'Warranty Conversion',   color: '#3b82f6' },
                                { dataKey: 'lostAmcConversion',    name: 'Lost AMC Conversion',   color: '#f59e0b' },
                                { dataKey: 'lostWarrantyConversion', name: 'Lost Warranty Conversion', color: '#ef4444' },
                            ]}
                            yAxisFormatter={formatCurrencyCompact}
                            valueFormatter={formatCurrency}
                        />

                        <StackedBarChart
                            data={chartData.contractsByBranchStacked}
                            title="Contracts by Branch"
                            stacks={[
                                { dataKey: 'amcRenewal',           name: 'AMC Renewal',           color: '#10b981' },
                                { dataKey: 'warrantyConversion',   name: 'Warranty Conversion',   color: '#3b82f6' },
                                { dataKey: 'lostAmcConversion',    name: 'Lost AMC Conversion',   color: '#f59e0b' },
                                { dataKey: 'lostWarrantyConversion', name: 'Lost Warranty Conversion', color: '#ef4444' },
                            ]}
                        />

                        <AreaChart
                            data={chartData.contractTimeline}
                            title="Contract Timeline"
                            xAxisTitle="Month"
                            yAxisTitleLeft="Contracts"
                            yAxisTitleRight="Revenue (₹)"
                            yAxisFormatterLeft={formatNumberCompact}
                            yAxisFormatterRight={formatCurrencyCompact}
                            valueFormatter={formatNumberCompact}
                            areas={[
                                { dataKey: 'count',   name: 'Count',   color: COLORS.chart?.[0] || '#8b5cf6', yAxisId: 'left' },
                                { dataKey: 'revenue', name: 'Revenue', color: COLORS.chart?.[1] || '#06b6d4', yAxisId: 'right' },
                            ]}
                        />

                        <DonutChart
                            data={chartData.revenueByVertical}
                            title="Revenue by Vertical"
                            valueFormatter={formatCurrency}
                            onSegmentClick={handleVerticalClick}
                        />
                    </div>
                )}

                {/* Industry Breakdown Modal */}
                {showIndustryModal && selectedVerticalData && (
                    <div
                        className="fixed inset-0 flex items-center justify-center z-50 p-4 backdrop-blur-sm"
                        style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
                        onClick={() => setShowIndustryModal(false)}
                    >
                        <div
                            className="bg-white rounded-xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                                <div>
                                    <h2 className="text-2xl font-bold text-gray-800">
                                        {selectedVerticalData.verticalName} - Industry Breakdown
                                    </h2>
                                    <p className="text-sm text-gray-600 mt-1">
                                        Total Revenue: {formatCurrency(selectedVerticalData.totalRevenue)}
                                    </p>
                                </div>
                                <button
                                    onClick={() => setShowIndustryModal(false)}
                                    className="text-gray-400 hover:text-gray-600 transition p-2 hover:bg-gray-100 rounded-full"
                                >
                                    <X className="w-6 h-6" />
                                </button>
                            </div>

                            <div className="flex-1 overflow-auto p-6">
                                <PieChart
                                    data={selectedVerticalData.industries}
                                    title="Revenue Distribution by Industry"
                                    valueFormatter={formatCurrency}
                                    height={400}
                                />
                            </div>

                            <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end">
                                <button
                                    onClick={() => setShowIndustryModal(false)}
                                    className="px-4 py-2 text-white rounded-md hover:opacity-90 transition font-medium"
                                    style={{ backgroundColor: COLORS.primary }}
                                >
                                    Close
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                <DataTable
                    title="Branches Overview"
                    columns={branchColumns}
                    data={sortedBranches}
                    sortConfig={sortConfig}
                    onSort={handleSort}
                    onRowClick={(row) => handleBranchClick(row.branchId)}
                    actionButton={{
                        label: 'View Details',
                        onClick: (row) => handleBranchClick(row.branchId),
                    }}
                />
            </div>
        </div>
    );
}