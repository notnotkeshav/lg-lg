// src/pages/Region.jsx
import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { IndianRupee, FileText, Users, Target, X } from 'lucide-react';
import { useRegionData, formatCurrency } from '../hooks/useFrappeData';
import { useFilters } from '../contexts/FilterContext';
import { COLORS } from '../constants/theme';
import { filterContractsLastNMonths, createContractTimeline } from '../utils/dateUtils';
import KPICard from '../components/common/KPICard';
import FilterPanel from '../components/common/FilterPanel';
import StackedBarChart, { formatCurrencyCompact, formatNumberCompact } from '../components/charts/StackedBarChart';
import DonutChart from '../components/charts/DonutChart';
import AreaChart from '../components/charts/AreaChart';
import PieChart from '../components/charts/PieChart';
import Breadcrumb from '../components/common/BreadCrumb';
import DataTable from '../components/common/DataTable2';

const REGION_HIERARCHY = {
    'EAST': ['EAST-1', 'EAST-2'],
    'NORTH': ['NORTH-1', 'NORTH-2']
};

export default function Region() {
    const { regionId } = useParams();
    const navigate = useNavigate();
    const { globalFilters, updateFilters, resetFilters } = useFilters();

    const [localFilters, setLocalFilters] = useState(globalFilters);
    const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
    const [managerSortConfig, setManagerSortConfig] = useState({ key: null, direction: 'asc' });
    const [viewMode, setViewMode] = useState('branches'); // 'branches' or 'managers'
    const [showIndustryModal, setShowIndustryModal] = useState(false);
    const [selectedVerticalData, setSelectedVerticalData] = useState(null);

    useEffect(() => {
        setLocalFilters(globalFilters);
    }, [globalFilters]);

    const { data, isLoading, error } = useRegionData(regionId, globalFilters);

    // Check if this is a parent region
    const isParentRegion = REGION_HIERARCHY[regionId] !== undefined;
    const displayRegionName = isParentRegion
        ? `${regionId} (${REGION_HIERARCHY[regionId].join(', ')})`
        : regionId;

    const handleApplyFilters = () => {
        updateFilters(localFilters);
    };

    const handleResetFilters = () => {
        setLocalFilters({});
        resetFilters();
    };

    const handleBranchClick = (branchId, dealType = null) => {
        if (dealType) {
            const newFilters = { ...globalFilters, dealType };
            updateFilters(newFilters);
        }
        navigate(`/branch/${branchId}`);
    };

    const handleManagerClick = (managerId, managerName) => {
        navigate(`/manager/${managerId}`, {
            state: {
                regionId,
                managerName,
                branchHeadId: managerId
            }
        });
    };

    const handleStackClick = (entry) => {
        const dealTypeMap = {
            'amcRenewal': 'AMC Renewal',
            'warrantyConversion': 'Warranty Conversion',
            'lostAmcConversion': 'Lost AMC Conversion',
            'lostWarrantyConversion': 'Lost Warranty Conversion'
        };

        const dealType = dealTypeMap[entry.stackKey];
        handleBranchClick(entry.branchId, dealType);
    };

    const handleSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });
    };

    const handleManagerSort = (key) => {
        let direction = 'asc';
        if (managerSortConfig.key === key && managerSortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setManagerSortConfig({ key, direction });
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

    const CONTRACT_STATUS_LABEL = {
        Active: 'Active Contracts',
        Expired: 'Expired Contracts',
        Total: 'Total Contracts',
    };

    const contractKpiTitle = CONTRACT_STATUS_LABEL[globalFilters.contractStatus] ?? 'Active Contracts';

    // Chart calculations
    const chartData = useMemo(() => {
        if (!data) return null;

        const { rawData } = data;

        // Use customer PO date if filter is enabled
        const useCustomerPoDate = globalFilters.useCustomerPoDate || false;

        // Filter contracts for last 12 months
        const filteredContracts = filterContractsLastNMonths(rawData.contracts, 12, useCustomerPoDate);

        const revenueByVertical = () => {
            const map = new Map();
            filteredContracts.forEach(c => {
                const v = c.parent_vertical || 'Uncategorized';
                map.set(v, (map.get(v) || 0) + parseFloat(c.amount || 0));
            });
            return Array.from(map, ([name, value]) => ({ name, value }));
        };

        // Store industry data for each vertical
        const industryByVertical = () => {
            const verticalMap = new Map();

            filteredContracts.forEach(c => {
                const vertical = c.parent_vertical || 'Uncategorized';
                const industry = c.industry || 'Unknown';

                if (!verticalMap.has(vertical)) {
                    verticalMap.set(vertical, new Map());
                }

                const industryMap = verticalMap.get(vertical);
                industryMap.set(industry, (industryMap.get(industry) || 0) + parseFloat(c.amount || 0));
            });

            // Convert to object format
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

        // Use utility function for contract timeline
        const contractTimelineData = createContractTimeline(filteredContracts, 12, useCustomerPoDate);

        const contractsByBranchStacked = () => {
            const branchMap = new Map();

            data.branches.forEach(b => {
                branchMap.set(b.branchId, {
                    name: b.branchName,
                    branchId: b.branchId,
                    amcRenewal: 0,
                    warrantyConversion: 0,
                    lostAmcConversion: 0,
                    lostWarrantyConversion: 0,
                });
            });

            filteredContracts.forEach(contract => {
                if (contract.branch && branchMap.has(contract.branch)) {
                    const branch = branchMap.get(contract.branch);
                    const type = (contract.deal_type || "").toLowerCase().trim();

                    if (type === "amc renewal") branch.amcRenewal += 1;
                    else if (type === "warranty conversion" || type === "warranty amc conversion") branch.warrantyConversion += 1;
                    else if (type === "lost amc conversion") branch.lostAmcConversion += 1;
                    else if (type === "lost warranty conversion") branch.lostWarrantyConversion += 1;
                }
            });

            return Array.from(branchMap.values());
        };

        const revenueByBranchStacked = () => {
            const branchMap = new Map();

            data.branches.forEach(b => {
                branchMap.set(b.branchId, {
                    name: b.branchName,
                    branchId: b.branchId,
                    amcRenewal: 0,
                    warrantyConversion: 0,
                    lostAmcConversion: 0,
                    lostWarrantyConversion: 0,
                });
            });

            filteredContracts.forEach(contract => {
                if (contract.branch && branchMap.has(contract.branch)) {
                    const branch = branchMap.get(contract.branch);
                    const amount = parseFloat(contract.amount || 0);
                    const type = (contract.deal_type || "").toLowerCase().trim();

                    if (type === "amc renewal") branch.amcRenewal += amount;
                    else if (type === "warranty conversion" || type === "warranty amc conversion") branch.warrantyConversion += amount;
                    else if (type === "lost amc conversion") branch.lostAmcConversion += amount;
                    else if (type === "lost warranty conversion") branch.lostWarrantyConversion += amount;
                }
            });

            return Array.from(branchMap.values());
        };

        return {
            revenueByVertical: revenueByVertical(),
            industryByVertical: industryByVertical(),
            dealStatus: dealStatus(),
            contractTimeline: contractTimelineData,
            contractsByBranchStacked: contractsByBranchStacked(),
            revenueByBranchStacked: revenueByBranchStacked()
        };
    }, [data, globalFilters.useCustomerPoDate]);

    // Sorted branches
    const sortedBranches = useMemo(() => {
        if (!data) return [];

        const branchMap = new Map();

        data.branches.forEach(b => {
            branchMap.set(b.branchId, {
                branchId: b.branchId,
                branchName: b.branchName,
                branchHead: b.branchHead,
                revenue: 0,
                contracts: 0,
                customers: 0,
                deals: 0,
                totalHP: 0,
                amcRenewal: 0,
                warrantyConversion: 0,
                lostAmcConversion: 0,
                lostWarrantyConversion: 0
            });
        });

        data.rawData.contracts.forEach(contract => {
            if (!contract.branch || !branchMap.has(contract.branch)) return;

            const branch = branchMap.get(contract.branch);
            branch.revenue += parseFloat(contract.amount || 0);
            branch.contracts += 1;
            branch.totalHP += parseFloat(contract.total_hp || 0);

            const type = (contract.deal_type || "").toLowerCase().trim();
            if (type === "amc renewal") branch.amcRenewal++;
            else if (type === "warranty conversion" || type === "warranty amc conversion") branch.warrantyConversion++;
            else if (type === "lost amc conversion") branch.lostAmcConversion++;
            else if (type === "lost warranty conversion") branch.lostWarrantyConversion++;
        });

        data.rawData.deals.forEach(deal => {
            if (deal.branch && branchMap.has(deal.branch)) {
                branchMap.get(deal.branch).deals++;
            }
        });

        data.rawData.organizations.forEach(org => {
            if (org.branch && branchMap.has(org.branch)) {
                branchMap.get(org.branch).customers++;
            }
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
    }, [data, sortConfig]);

    // Sorted area managers (aggregated by branch_head from branches)
    const sortedManagers = useMemo(() => {
        if (!data) return [];

        const managerMap = new Map();

        // First, create manager entries from branches (branch_head is the area manager)
        data.branches.forEach(branch => {
            const branchHeadId = branch.branchHead;
            const branchHeadName = branch.branchHead;

            if (!branchHeadId || branchHeadId === 'Administrator') return;

            if (!managerMap.has(branchHeadId)) {
                managerMap.set(branchHeadId, {
                    managerId: branchHeadId,
                    managerName: branchHeadName,
                    revenue: 0,
                    contracts: 0,
                    deals: 0,
                    customers: new Set(),
                    branches: new Set(),
                    branchNames: new Set(),
                    amcRenewal: 0,
                    warrantyConversion: 0,
                    lostAmcConversion: 0,
                    lostWarrantyConversion: 0
                });
            }

            const manager = managerMap.get(branchHeadId);
            manager.branches.add(branch.branchId);
            manager.branchNames.add(branch.branchName);
        });

        // Now aggregate contract data by branch, then roll up to managers
        data.rawData.contracts.forEach(contract => {
            if (!contract.branch) return;

            const branch = data.branches.find(b => b.branchId === contract.branch);
            if (!branch || !branch.branchHead) return;

            const branchHeadId = branch.branchHead;
            if (!managerMap.has(branchHeadId)) return;

            const manager = managerMap.get(branchHeadId);
            manager.revenue += parseFloat(contract.amount || 0);
            manager.contracts += 1;

            if (contract.customer) {
                manager.customers.add(contract.customer);
            }

            const type = (contract.deal_type || "").toLowerCase().trim();
            if (type === "amc renewal") manager.amcRenewal++;
            else if (type === "warranty conversion" || type === "warranty amc conversion") manager.warrantyConversion++;
            else if (type === "lost amc conversion") manager.lostAmcConversion++;
            else if (type === "lost warranty conversion") manager.lostWarrantyConversion++;
        });

        // Aggregate deals
        data.rawData.deals.forEach(deal => {
            if (!deal.branch) return;

            const branch = data.branches.find(b => b.branchId === deal.branch);
            if (!branch || !branch.branchHead) return;

            const branchHeadId = branch.branchHead;
            if (managerMap.has(branchHeadId)) {
                managerMap.get(branchHeadId).deals++;
            }
        });

        // Convert Sets to counts/arrays
        managerMap.forEach(manager => {
            manager.customers = manager.customers.size;
            manager.totalBranches = manager.branches.size;
            manager.branchList = Array.from(manager.branchNames).join(', ');
            delete manager.branches;
            delete manager.branchNames;
        });

        let result = Array.from(managerMap.values());

        if (managerSortConfig.key) {
            result.sort((a, b) => {
                if (a[managerSortConfig.key] < b[managerSortConfig.key]) return managerSortConfig.direction === 'asc' ? -1 : 1;
                if (a[managerSortConfig.key] > b[managerSortConfig.key]) return managerSortConfig.direction === 'asc' ? 1 : -1;
                return 0;
            });
        }

        return result;
    }, [data, managerSortConfig]);

    const branchColumns = [
        { key: 'branchName', label: 'Branch', bold: true },
        { key: 'branchHead', label: 'Area Manager' },
        { key: 'revenue', label: 'Revenue', align: 'right', render: v => formatCurrency(v) },
        { key: 'contracts', label: 'Total Contracts', align: 'right' },
        { key: 'amcRenewal', label: 'AMC Renewal', align: 'right' },
        { key: 'warrantyConversion', label: 'Warranty Conversion', align: 'right' },
        { key: 'lostAmcConversion', label: 'Lost AMC Conversion', align: 'right' },
        { key: 'lostWarrantyConversion', label: 'Lost Warranty Conversion', align: 'right' },
    ];

    const managerColumns = [
        { key: 'managerName', label: 'Area Manager', bold: true },
        { key: 'totalBranches', label: 'Branches', align: 'right' },
        { key: 'revenue', label: 'Revenue', align: 'right', render: v => formatCurrency(v) },
        { key: 'contracts', label: 'Total Contracts', align: 'right' },
        { key: 'amcRenewal', label: 'AMC Renewal', align: 'right' },
        { key: 'warrantyConversion', label: 'Warranty Conversion', align: 'right' },
        { key: 'lostAmcConversion', label: 'Lost AMC Conversion', align: 'right' },
        { key: 'lostWarrantyConversion', label: 'Lost Warranty Conversion', align: 'right' },
    ];

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-xl font-semibold" style={{ color: COLORS.text.secondary }}>
                    Loading region data...
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="bg-white rounded-lg shadow-md p-6 max-w-md">
                    <h3 className="text-xl font-semibold text-red-600 mb-2">Error Loading Region</h3>
                    <p className="text-gray-600">{error.message}</p>
                </div>
            </div>
        );
    }

    if (!data) return null;

    return (
        <div className="min-h-screen" style={{ backgroundColor: COLORS.background }}>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                <div className="mb-6">
                    <Breadcrumb
                        items={[
                            { label: 'Region', href: -1 },
                            { label: displayRegionName }
                        ]}
                    />
                    <h1 className="text-3xl font-bold" style={{ color: COLORS.text.primary }}>
                        {displayRegionName} Dashboard
                    </h1>
                    <p className="text-gray-600 mt-1">
                        {isParentRegion
                            ? `Aggregated view of ${REGION_HIERARCHY[regionId].join(' and ')}`
                            : `Detailed view of ${regionId}`
                        }
                    </p>
                </div>

                <FilterPanel
                    filters={localFilters}
                    setFilters={setLocalFilters}
                    onApply={handleApplyFilters}
                    onReset={handleResetFilters}
                />

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
                    <KPICard
                        title="Total Revenue"
                        value={formatCurrency(data.summary.totalRevenue)}
                        subtitle={`Avg: ${formatCurrency(data.summary.avgContractValue)}`}
                        icon={IndianRupee}
                    />
                    <KPICard
                        title={contractKpiTitle}
                        value={data.summary.totalContracts.toLocaleString()}
                        subtitle={`All statuses: ${data.summary.totalContractsAll.toLocaleString()}`}
                        icon={FileText}
                    />
                    <KPICard
                        title="Total Customers"
                        value={data.summary.totalCustomers.toLocaleString()}
                        icon={Users}
                    />
                    <KPICard
                        title="Active Opportunities"
                        value={data.summary.totalDeals.toLocaleString()}
                        subtitle={`Quotes: ${data.summary.totalQuotations.toLocaleString()}`}
                        icon={Target}
                    />
                </div>

                {chartData && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <StackedBarChart
                            data={chartData.revenueByBranchStacked}
                            title="Revenue by Branch"
                            stacks={[
                                { dataKey: 'amcRenewal', name: 'AMC Renewal', color: '#10b981' },
                                { dataKey: 'warrantyConversion', name: 'Warranty Conversion', color: '#3b82f6' },
                                { dataKey: 'lostAmcConversion', name: 'Lost AMC Conversion', color: '#f59e0b' },
                                { dataKey: 'lostWarrantyConversion', name: 'Lost Warranty Conversion', color: '#ef4444' },
                            ]}
                            onBarClick={handleStackClick}
                            yAxisFormatter={formatCurrencyCompact}
                            valueFormatter={formatCurrency}
                        />

                        <StackedBarChart
                            data={chartData.contractsByBranchStacked}
                            title="Contracts by Branch"
                            stacks={[
                                { dataKey: 'amcRenewal', name: 'AMC Renewal', color: '#10b981' },
                                { dataKey: 'warrantyConversion', name: 'Warranty Conversion', color: '#3b82f6' },
                                { dataKey: 'lostAmcConversion', name: 'Lost AMC Conversion', color: '#f59e0b' },
                                { dataKey: 'lostWarrantyConversion', name: 'Lost Warranty Conversion', color: '#ef4444' },
                            ]}
                            onBarClick={handleStackClick}
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
                                {
                                    dataKey: "count",
                                    name: "Count",
                                    color: COLORS.chart?.[0] || "#8b5cf6",
                                    yAxisId: "left"
                                },
                                {
                                    dataKey: "revenue",
                                    name: "Revenue",
                                    color: COLORS.chart?.[1] || "#06b6d4",
                                    yAxisId: "right"
                                }
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

                {/* View Mode Toggle */}
                <div className="mb-4 flex gap-2">
                    <button
                        onClick={() => setViewMode('branches')}
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${viewMode === 'branches'
                            ? 'text-white'
                            : 'bg-white border hover:bg-gray-50'
                            }`}
                        style={{
                            backgroundColor: viewMode === 'branches' ? COLORS.primary : 'white',
                            borderColor: COLORS.border,
                            color: viewMode === 'branches' ? 'white' : COLORS.text.secondary
                        }}
                    >
                        Branch View ({sortedBranches.length})
                    </button>
                    <button
                        onClick={() => setViewMode('managers')}
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${viewMode === 'managers'
                            ? 'text-white'
                            : 'bg-white border hover:bg-gray-50'
                            }`}
                        style={{
                            backgroundColor: viewMode === 'managers' ? COLORS.primary : 'white',
                            borderColor: COLORS.border,
                            color: viewMode === 'managers' ? 'white' : COLORS.text.secondary
                        }}
                    >
                        Area Manager View ({sortedManagers.length})
                    </button>
                </div>

                {/* Tables */}
                {viewMode === 'branches' ? (
                    <DataTable
                        title="Branches Overview"
                        columns={branchColumns}
                        data={sortedBranches}
                        sortConfig={sortConfig}
                        onSort={handleSort}
                        onRowClick={(row) => handleBranchClick(row.branchId)}
                        actionButton={{
                            label: 'View Details',
                            onClick: (row) => handleBranchClick(row.branchId)
                        }}
                    />
                ) : (
                    <DataTable
                        title="Area Managers Overview"
                        columns={managerColumns}
                        data={sortedManagers}
                        sortConfig={managerSortConfig}
                        onSort={handleManagerSort}
                        onRowClick={(row) => handleManagerClick(row.managerId, row.managerName)}
                        actionButton={{
                            label: 'View Details',
                            onClick: (row) => handleManagerClick(row.managerId, row.managerName)
                        }}
                    />
                )}
            </div>
        </div>
    );
}