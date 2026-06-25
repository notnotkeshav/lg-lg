// src/pages/Homepage.jsx
import React, { useState, useMemo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { IndianRupee, FileText, Users, Target, X } from 'lucide-react';
import { useCountryData, formatCurrency } from '../hooks/useFrappeData';
import { useFilters } from '../contexts/FilterContext';
import { COLORS } from '../constants/theme';
import { filterContractsLastNMonths, createContractTimeline } from '../utils/dateUtils';
import KPICard from '../components/common/KPICard';
import FilterPanel from '../components/common/FilterPanel';
import StackedBarChart, { formatCurrencyCompact, formatNumberCompact } from '../components/charts/StackedBarChart';
import SmoothLineChart from '../components/charts/SmoothLineChart';
import PieChart from '../components/charts/PieChart';
import DataTable from '../components/common/DataTable2';
import Breadcrumb from '@/components/common/BreadCrumb';

export default function Homepage() {
    const navigate = useNavigate();
    const { globalFilters, updateFilters, resetFilters } = useFilters();

    const [localFilters, setLocalFilters] = useState(globalFilters);
    const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
    const [showIndustryModal, setShowIndustryModal] = useState(false);
    const [selectedVerticalData, setSelectedVerticalData] = useState(null);

    useEffect(() => {
        setLocalFilters(globalFilters);
    }, [globalFilters]);

    const { data, isLoading, error } = useCountryData(globalFilters);

    const handleApplyFilters = () => {
        updateFilters(localFilters);
    };

    const handleResetFilters = () => {
        setLocalFilters({});
        resetFilters();
    };

    const handleRegionClick = (regionId, dealType = null) => {
        if (dealType) {
            const newFilters = { ...globalFilters, dealType };
            updateFilters(newFilters);
        }
        navigate(`/region/${regionId}`);
    };

    const handleStackClick = (entry) => {
        const dealTypeMap = {
            amcRenewal: 'AMC Renewal',
            warrantyConversion: 'Warranty Conversion',
            lostAmcConversion: 'Lost AMC Conversion',
            lostWarrantyConversion: 'Lost Warranty Conversion'
        };

        const dealType = dealTypeMap[entry.stackKey];
        handleRegionClick(entry.regionId, dealType);
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

    const CONTRACT_STATUS_LABEL = {
        Active: 'Active Contracts',
        Expired: 'Expired Contracts',
        Total: 'Total Contracts',
    };
    
    const contractKpiTitle = CONTRACT_STATUS_LABEL[globalFilters.contractStatus] ?? 'Active Contracts';

    const chartData = useMemo(() => {
        if (!data) return null;

        const { rawData } = data;

        // Use customer PO date if filter is enabled
        const useCustomerPoDate = globalFilters.useCustomerPoDate || false;

        // Filter contracts for last 12 months (excluding future dates)
        const filteredContracts = filterContractsLastNMonths(rawData.contracts, 12, useCustomerPoDate);

        const chartRegions = data.regions;

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

        // Use utility function for contract timeline
        const contractTimelineData = createContractTimeline(filteredContracts, 12, useCustomerPoDate);

        const contractsByRegionStacked = chartRegions
            .filter(r => !r.isParent)
            .map(r => ({
                name: r.regionName,
                regionId: r.regionId,
                amcRenewal: r.amcRenewal || 0,
                warrantyConversion: r.warrantyConversion || 0,
                lostAmcConversion: r.lostAmcConversion || 0,
                lostWarrantyConversion: r.lostWarrantyConversion || 0
            }));

        const revenueByRegionStacked = chartRegions
            .filter(r => !r.isParent)
            .map(r => ({
                name: r.regionName,
                regionId: r.regionId,
                amcRenewal: 0,
                warrantyConversion: 0,
                lostAmcConversion: 0,
                lostWarrantyConversion: 0
            }));

        const categorizeDealType = (dealType) => {
            const type = (dealType || "").toLowerCase().trim();

            if (type === "amc renewal") return 'amcRenewal';
            if (type === "warranty conversion" || type === "warranty amc conversion") return 'warrantyConversion';
            if (type === "lost amc conversion") return 'lostAmcConversion';
            if (type === "lost warranty conversion") return 'lostWarrantyConversion';
        };

        // Aggregate contracts for revenue chart (only for leaf regions)
        filteredContracts.forEach(contract => {
            const region = chartRegions.find(r => r.regionId === contract.region && !r.isParent);

            if (region) {
                const revenueRegion = revenueByRegionStacked.find(cr => cr.regionId === region.regionId);

                if (revenueRegion) {
                    const amount = parseFloat(contract.amount || 0);
                    const category = categorizeDealType(contract.deal_type);

                    // Add to revenue chart
                    revenueRegion[category] += amount;
                }
            }
        });

        return {
            revenueByVertical: revenueByVertical(),
            industryByVertical: industryByVertical(),
            contractTimeline: contractTimelineData,
            contractsByRegionStacked,
            revenueByRegionStacked
        };
    }, [data, globalFilters.useCustomerPoDate]);

    // Sorted regions - exclude child regions from top-level, they'll appear under parents
    const sortedRegions = useMemo(() => {
        if (!data) return [];

        // Filter out child regions - they'll be shown under their parents
        let topLevelRegions = data.regions.filter(r => !r.parentRegionId);

        if (sortConfig.key) {
            topLevelRegions.sort((a, b) => {
                if (a[sortConfig.key] < b[sortConfig.key]) return sortConfig.direction === 'asc' ? -1 : 1;
                if (a[sortConfig.key] > b[sortConfig.key]) return sortConfig.direction === 'asc' ? 1 : -1;
                return 0;
            });
        }

        // Build final array with parent regions followed by their children
        const result = [];
        topLevelRegions.forEach(region => {
            result.push(region);

            if (region.isParent && region.subRegions) {
                region.subRegions.forEach(subRegionId => {
                    const subRegion = data.regions.find(r => r.regionId === subRegionId);
                    if (subRegion) result.push(subRegion);
                });
            }
        });

        return result;
    }, [data, sortConfig]);

    const regionColumns = [
        { key: "regionName", label: "Region", bold: true },
        { key: "regionHead", label: "Region Head" },
        { key: "revenue", label: "Revenue", align: "right", render: v => formatCurrency(v) },
        { key: "contracts", label: "Total Contracts", align: "right" },
        { key: "amcRenewal", label: "AMC Renewal", align: "right" },
        { key: "warrantyConversion", label: "Warranty Conversion", align: "right" },
        { key: "lostAmcConversion", label: "Lost AMC Conversion", align: "right" },
        { key: "lostWarrantyConversion", label: "Lost Warranty Conversion", align: "right" },
    ];

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-xl font-semibold" style={{ color: COLORS.text.secondary }}>
                    Loading dashboard...
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="bg-white rounded-lg shadow-md p-6 max-w-md">
                    <h3 className="text-xl font-semibold text-red-600 mb-2">Error Loading Dashboard</h3>
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
                    <Breadcrumb items={[]} />
                    <h1 className="text-3xl font-bold" style={{ color: COLORS.text.primary }}>
                        All India Dashboard
                    </h1>
                    <p className="text-gray-600 mt-1">National overview of all regions</p>
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
                        <StackedBarChart
                            data={chartData.revenueByRegionStacked}
                            title="Revenue by Region"
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
                            data={chartData.contractsByRegionStacked}
                            title="Contracts by Region"
                            stacks={[
                                { dataKey: 'amcRenewal', name: 'AMC Renewal', color: '#10b981' },
                                { dataKey: 'warrantyConversion', name: 'Warranty Conversion', color: '#3b82f6' },
                                { dataKey: 'lostAmcConversion', name: 'Lost AMC Conversion', color: '#f59e0b' },
                                { dataKey: 'lostWarrantyConversion', name: 'Lost Warranty Conversion', color: '#ef4444' },
                            ]}
                            onBarClick={handleStackClick}
                        />

                        <SmoothLineChart
                            data={chartData.contractTimeline}
                            title="Contract Timeline (Last 12 Months)"
                            xAxisTitle="Month"
                            yAxisTitleLeft="Contracts"
                            yAxisTitleRight="Revenue"
                            yAxisFormatterLeft={formatNumberCompact}
                            yAxisFormatterRight={formatCurrencyCompact}
                            lines={[
                                { dataKey: 'count', name: 'Count', color: COLORS.chart?.[0] || '#8b5cf6' },
                                { dataKey: 'revenue', name: 'Revenue', color: COLORS.chart?.[1] || '#06b6d4', yAxisId: 'right' }
                            ]}
                            valueFormatter={(v, key) => key === 'revenue' ? formatCurrency(v) : v}
                        />

                        <PieChart
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
                    title="Regions Overview"
                    columns={regionColumns}
                    data={sortedRegions}
                    sortConfig={sortConfig}
                    onSort={handleSort}
                    onRowClick={(row) => handleRegionClick(row.regionId)}
                    actionButton={{
                        label: 'View Details',
                        onClick: (row) => handleRegionClick(row.regionId)
                    }}
                />
            </div>
        </div>
    );
}