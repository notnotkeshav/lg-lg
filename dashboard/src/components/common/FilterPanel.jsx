// src/components/common/FilterPanel.jsx
import React, { useCallback } from 'react';
import { Filter, X } from 'lucide-react';
import { COLORS } from '../../constants/theme';
import DateRangeInput from './DateRangeInput';
import MultiSelect from './MultiSelect';
import { useFilterOptions } from '../../hooks/useFilterOptions';

const CONTRACT_STATUS_OPTIONS = [
    { value: 'Active',  label: 'Active' },
    { value: 'Expired', label: 'Expired' },
    { value: 'Total',   label: 'Total (Both)' },
];

const asArray = (v) => {
    if (!v) return [];
    if (Array.isArray(v)) return v;
    return [v];
};

export default function FilterPanel({ filters, setFilters, onApply, onReset, additionalOptions = {} }) {
    const { verticals, dealTypes, statuses, isLoading, error } = useFilterOptions();
    const branches = additionalOptions.branches || [];

    const handleFilterChange = useCallback((key, value) => {
        setFilters(prev => ({ ...prev, [key]: value }));
    }, [setFilters]);

    const handleDateRangeChange = useCallback(({ startDate, endDate }) => {
        setFilters(prev => ({ ...prev, startDate, endDate }));
    }, [setFilters]);

    const activeFilterCount = [
        (filters.startDate || filters.endDate) ? 1 : 0,
        asArray(filters.vertical).length  > 0  ? 1 : 0,
        asArray(filters.dealType).length  > 0  ? 1 : 0,
        asArray(filters.status).length    > 0  ? 1 : 0,
        (asArray(filters.contractStatus).length > 0 &&
            !(asArray(filters.contractStatus).length === 1 && filters.contractStatus[0] === 'Active')) ? 1 : 0,
        asArray(filters.branch).length    > 0  ? 1 : 0,
        (filters.customerPoStartDate || filters.customerPoEndDate) ? 1 : 0,
    ].reduce((a, b) => a + b, 0);

    if (error) {
        return (
            <div className="bg-white rounded-lg shadow-md p-6 mb-6 border border-red-200">
                Error loading filters: {error.message}
            </div>
        );
    }

    const gridCols = branches.length > 0 ? 'lg:grid-cols-7' : 'lg:grid-cols-6';

    return (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <Filter className="h-5 w-5" style={{ color: COLORS.primary }} />
                    <h3 className="text-lg font-semibold">Filters</h3>
                    {activeFilterCount > 0 && (
                        <span className="text-xs px-2 py-0.5 rounded-full font-medium"
                              style={{ backgroundColor: COLORS.primary, color: 'white' }}>
                            {activeFilterCount} active
                        </span>
                    )}
                </div>
                <button onClick={onReset}
                        className="flex items-center gap-2 px-3 py-1.5 text-sm rounded-md border hover:bg-gray-50"
                        style={{ borderColor: COLORS.border }}>
                    <X className="h-4 w-4" />
                    Clear All
                </button>
            </div>

            <div className={`grid grid-cols-1 md:grid-cols-2 ${gridCols} gap-4`}>
                <DateRangeInput
                    startDate={filters.startDate}
                    endDate={filters.endDate}
                    onChange={handleDateRangeChange}
                />

                <div>
                    <label className="text-sm font-medium mb-2 block">Vertical</label>
                    <MultiSelect
                        options={verticals}
                        value={asArray(filters.vertical)}
                        onChange={v => handleFilterChange('vertical', v)}
                        placeholder="All Verticals"
                        allLabel="All Verticals"
                    />
                </div>

                <div>
                    <label className="text-sm font-medium mb-2 block">Contract Type</label>
                    <MultiSelect
                        options={dealTypes}
                        value={asArray(filters.dealType)}
                        onChange={v => handleFilterChange('dealType', v)}
                        placeholder="All Types"
                        allLabel="All Types"
                    />
                </div>

                <div>
                    <label className="text-sm font-medium mb-2 block">Deal Status</label>
                    <MultiSelect
                        options={statuses}
                        value={asArray(filters.status)}
                        onChange={v => handleFilterChange('status', v)}
                        placeholder="All Status"
                        allLabel="All Status"
                    />
                </div>

                <div>
                    <label className="text-sm font-medium mb-2 block">Contract Status</label>
                    <MultiSelect
                        options={CONTRACT_STATUS_OPTIONS}
                        value={asArray(filters.contractStatus)}
                        onChange={v => handleFilterChange('contractStatus', v)}
                        placeholder="Active (default)"
                        allLabel="All (Active + Expired)"
                        singleSelect
                    />
                </div>

                {branches.length > 0 && (
                    <div>
                        <label className="text-sm font-medium mb-2 block">Branch</label>
                        <MultiSelect
                            options={branches.map(b => ({ value: b.value ?? b.branchId, label: b.label ?? b.branchName }))}
                            value={asArray(filters.branch)}
                            onChange={v => handleFilterChange('branch', v)}
                            placeholder="All Branches"
                            allLabel="All Branches"
                        />
                    </div>
                )}

                <div className="flex items-end">
                    <button onClick={onApply}
                            className="w-full px-4 py-2 text-sm font-medium text-white rounded-md"
                            style={{ backgroundColor: COLORS.primary }}>
                        Apply Filters
                    </button>
                </div>
            </div>

            <div className="mt-4 pt-4 border-t" style={{ borderColor: COLORS.border }}>
                <div className="flex items-center gap-3 mb-3">
                    <label className="flex items-center gap-2 text-sm cursor-pointer select-none">
                        <input
                            type="checkbox"
                            checked={filters.useCustomerPoDate || false}
                            onChange={(e) => handleFilterChange('useCustomerPoDate', e.target.checked)}
                        />
                        <span className="font-medium">Filter by Customer PO Date</span>
                    </label>
                    {!filters.useCustomerPoDate && (
                        <span className="text-xs text-gray-400">
                            Enable to filter contracts by PO date from AMC Contract
                        </span>
                    )}
                </div>

                {filters.useCustomerPoDate && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <DateRangeInput
                            startDate={filters.customerPoStartDate}
                            endDate={filters.customerPoEndDate}
                            onChange={({ startDate, endDate }) => {
                                handleFilterChange('customerPoStartDate', startDate);
                                handleFilterChange('customerPoEndDate', endDate);
                            }}
                        />
                        <div className="flex items-end">
                            <p className="text-sm text-gray-500">
                                Showing contracts where Customer PO Date falls within the selected range.
                            </p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}