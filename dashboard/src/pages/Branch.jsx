// src/pages/Branch.jsx
import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { IndianRupee, FileText, Users, Target, X } from 'lucide-react';
import { useBranchData, formatCurrency } from '../hooks/useFrappeData';
import { useFilters } from '../contexts/FilterContext';
import { COLORS } from '../constants/theme';
import { filterContractsLastNMonths, createContractTimeline } from '../utils/dateUtils';
import KPICard from '../components/common/KPICard';
import FilterPanel from '../components/common/FilterPanel';
import DonutChart from '../components/charts/DonutChart';
import PieChart from '../components/charts/PieChart';
import AreaChart from '../components/charts/AreaChart';
import RoundedBarChart from '../components/charts/RoundedBarChart';
import { formatCurrencyCompact, formatNumberCompact } from '../components/charts/StackedBarChart';
import Breadcrumb from '../components/common/BreadCrumb';
import DataTable from '../components/common/DataTable';

// Deal type display order and colours — single source of truth
const DEAL_TYPE_CONFIG = [
    { key: 'AMC Renewal',           color: '#10b981' },
    { key: 'Warranty Conversion',   color: '#3b82f6' },
    { key: 'Lost AMC Conversion',   color: '#f59e0b' },
    { key: 'Lost Warranty Conversion', color: '#ef4444' },
];

export default function Branch() {
    const { branchId } = useParams();
    const navigate = useNavigate();
    const { globalFilters, updateFilters, resetFilters } = useFilters();

    const [localFilters, setLocalFilters] = useState(globalFilters);
    const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
    const [showIndustryModal, setShowIndustryModal] = useState(false);
    const [selectedVerticalData, setSelectedVerticalData] = useState(null);

    useEffect(() => {
        setLocalFilters(globalFilters);
    }, [globalFilters]);

    const { data, isLoading, error } = useBranchData(branchId, globalFilters);

    const handleApplyFilters = () => { updateFilters(localFilters); };

    const handleResetFilters = () => {
        setLocalFilters({});
        resetFilters();
    };

    const handleManagerClick = () => {
        if (!data?.branchInfo) return;

        const branchHeadId   = data.branchInfo.branch_head_id   || data.branchInfo.branch_head_name;
        const branchHeadName = data.branchInfo.branch_head_name || branchHeadId;
        const regionId       = data.branchInfo.region;

        updateFilters({ ...globalFilters, branch: branchId });

        navigate(`/manager/${branchHeadId}`, {
            state: { regionId, managerName: branchHeadName, branchHeadId }
        });
    };

    const handleVerticalClick = (segment) => {
        if (chartData?.industryByVertical) {
            setSelectedVerticalData({
                verticalName: segment.name,
                totalRevenue: segment.value,
                industries: chartData.industryByVertical[segment.name] || []
            });
            setShowIndustryModal(true);
        }
    };

    const CONTRACT_STATUS_LABEL = {
        Active: 'Active Contracts', Expired: 'Expired Contracts', Total: 'Total Contracts',
    };
    const contractKpiTitle = CONTRACT_STATUS_LABEL[globalFilters.contractStatus] ?? 'Active Contracts';

    const chartData = useMemo(() => {
        if (!data) return null;

        const { rawData } = data;
        const useCustomerPoDate = globalFilters.useCustomerPoDate || false;
        const filteredContracts = filterContractsLastNMonths(rawData.contracts, 12, useCustomerPoDate);

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

        const quotationStatus = () => {
            const map = new Map();
            rawData.quotations.forEach(q => {
                const s = q.status || 'Unknown';
                map.set(s, (map.get(s) || 0) + 1);
            });
            return Array.from(map, ([name, value]) => ({ name, value }));
        };

        const contractTimelineData = createContractTimeline(filteredContracts, 12, useCustomerPoDate);

        // RoundedBarChart format: one row per deal type, value field for the metric.
        // Use filteredContracts (last 12 months, status-filtered) to stay consistent
        // with every other chart on this page.
        const revenueByDealType = (() => {
            const totals = new Map(DEAL_TYPE_CONFIG.map(d => [d.key, 0]));
            filteredContracts.forEach(c => {
                const raw  = (c.deal_type || '').trim();
                // normalise "Warranty AMC Conversion" → "Warranty Conversion"
                const type = raw.toLowerCase() === 'warranty amc conversion'
                    ? 'Warranty Conversion'
                    : raw;
                if (totals.has(type)) totals.set(type, totals.get(type) + parseFloat(c.amount || 0));
            });
            return DEAL_TYPE_CONFIG
                .map(d => ({ name: d.key, value: totals.get(d.key), color: d.color }))
                .filter(d => d.value > 0);
        })();

        const contractsByDealType = (() => {
            const totals = new Map(DEAL_TYPE_CONFIG.map(d => [d.key, 0]));
            filteredContracts.forEach(c => {
                const raw  = (c.deal_type || '').trim();
                const type = raw.toLowerCase() === 'warranty amc conversion'
                    ? 'Warranty Conversion'
                    : raw;
                if (totals.has(type)) totals.set(type, totals.get(type) + 1);
            });
            return DEAL_TYPE_CONFIG
                .map(d => ({ name: d.key, value: totals.get(d.key), color: d.color }))
                .filter(d => d.value > 0);
        })();

        return {
            revenueByVertical: revenueByVertical(),
            industryByVertical: industryByVertical(),
            dealStatus: dealStatus(),
            quotationStatus: quotationStatus(),
            contractTimeline: contractTimelineData,
            revenueByDealType,
            contractsByDealType,
        };
    }, [data, globalFilters.useCustomerPoDate]);

    const branchHeadInfo = useMemo(() => {
        if (!data?.managers?.[0]) return [];
        const manager    = data.managers[0];
        const { rawData } = data;
        const breakdown  = { amcRenewal: 0, warrantyConversion: 0, lostAmcConversion: 0, lostWarrantyConversion: 0 };

        rawData.contracts.forEach(contract => {
            const type = (contract.deal_type || '').toLowerCase().trim();
            if      (type === 'amc renewal')                                          breakdown.amcRenewal++;
            else if (type === 'warranty conversion' || type === 'warranty amc conversion') breakdown.warrantyConversion++;
            else if (type === 'lost amc conversion')                                  breakdown.lostAmcConversion++;
            else if (type === 'lost warranty conversion')                             breakdown.lostWarrantyConversion++;
        });

        return [{
            managerName: manager.managerName,
            revenue:     manager.revenue,
            contracts:   manager.contracts,
            customers:   manager.customers,
            deals:       manager.deals,
            quotations:  manager.quotations,
            ...breakdown
        }];
    }, [data]);

    const branchHeadColumns = [
        { key: 'managerName',          label: 'Branch Head',        bold: true },
        { key: 'revenue',              label: 'Revenue',            align: 'right', render: v => formatCurrency(v) },
        { key: 'contracts',            label: 'Total Contracts',    align: 'right' },
        { key: 'amcRenewal',           label: 'AMC Renewal',        align: 'right' },
        { key: 'warrantyConversion',   label: 'Warranty Conv.',     align: 'right' },
        { key: 'lostAmcConversion',    label: 'Lost AMC Conv.',     align: 'right' },
        { key: 'lostWarrantyConversion', label: 'Lost Warranty Conv.', align: 'right' },
    ];

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-xl font-semibold" style={{ color: COLORS.text.secondary }}>
                    Loading branch data...
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="bg-white rounded-lg shadow-md p-6 max-w-md">
                    <h3 className="text-xl font-semibold text-red-600 mb-2">Error Loading Branch</h3>
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
                            ...(data?.branchInfo?.region
                                ? [{ label: data.branchInfo.region, href: `/region/${data.branchInfo.region}` }]
                                : []),
                            { label: data?.branchInfo?.branch_name || branchId }
                        ]}
                    />
                    <h1 className="text-3xl font-bold" style={{ color: COLORS.text.primary }}>
                        Branch Dashboard
                    </h1>
                    <p className="text-gray-600 mt-1">
                        {data?.branchInfo?.branch_name || branchId}
                        {data?.branchInfo?.branch_head_name && ` - Head: ${data.branchInfo.branch_head_name}`}
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
                        title="Total Opportunities"
                        value={data.summary.totalDeals.toLocaleString()}
                        subtitle={`Quotes: ${data.summary.totalQuotations.toLocaleString()}`}
                        icon={Target}
                    />
                </div>

                {chartData && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">

                        {/* Revenue by Deal Type — RoundedBarChart, one bar per deal type */}
                        <RoundedBarChart
                            data={chartData.revenueByDealType}
                            title="Revenue by Contract Type"
                            bars={[{
                                dataKey: 'value',
                                name: 'Revenue',
                                color: COLORS.primary,
                                formatter: formatCurrency,
                            }]}
                            yAxisFormatter={formatCurrencyCompact}
                            xAxisLabel="Contract Type"
                            yAxisLabel="Revenue"
                            height={350}
                        />

                        {/* Contracts by Deal Type */}
                        <RoundedBarChart
                            data={chartData.contractsByDealType}
                            title="Contracts by Contract Type"
                            bars={[{
                                dataKey: 'value',
                                name: 'Contracts',
                                color: COLORS.primary,
                            }]}
                            xAxisLabel="Contract Type"
                            yAxisLabel="Contracts"
                            height={350}
                        />

                        {/* Contract Timeline */}
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
                                { dataKey: 'count',   name: 'Count',   color: COLORS.chart?.[0] || '#8b5cf6', yAxisId: 'left'  },
                                { dataKey: 'revenue', name: 'Revenue', color: COLORS.chart?.[1] || '#06b6d4', yAxisId: 'right' },
                            ]}
                        />

                        {/* Revenue by Vertical */}
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

                {branchHeadInfo.length > 0 && (
                    <DataTable
                        title="Branch Head Overview"
                        columns={branchHeadColumns}
                        data={branchHeadInfo}
                        onRowClick={handleManagerClick}
                        actionButton={{
                            label: 'View Manager Details',
                            onClick: handleManagerClick
                        }}
                    />
                )}
            </div>
        </div>
    );
}