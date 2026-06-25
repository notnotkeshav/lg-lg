import React, { useState } from 'react';
import { ArrowUp, ArrowDown, ArrowUpDown, ChevronRight, ChevronDown } from 'lucide-react';
import { COLORS } from '../../constants/theme';

export default function DataTable({
    title,
    columns,
    data,
    onRowClick,
    actionButton,
    sortConfig,
    onSort
}) {
    const [expandedRows, setExpandedRows] = useState(new Set());

    const toggleRow = (regionId) => {
        const newExpanded = new Set(expandedRows);
        if (newExpanded.has(regionId)) {
            newExpanded.delete(regionId);
        } else {
            newExpanded.add(regionId);
        }
        setExpandedRows(newExpanded);
    };

    // Organize data into parent-child structure
    const organizedData = React.useMemo(() => {
        // Check if data is already organized (has parent-child structure)
        const hasParentChild = data.some(row => row.isParent || row.parentRegionId);

        if (!hasParentChild) {
            // Data is flat, return as-is
            return data;
        }

        // Data already has hierarchy, just return it
        // The parent component (Homepage) already organized it correctly
        return data;
    }, [data]);

    return (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-800">{title}</h3>
            </div>

            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            {columns.map((col, index) => (
                                <th
                                    key={index}
                                    onClick={() => col.sortable !== false && onSort && onSort(col.key)}
                                    className={`px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider ${col.align === 'right' ? 'text-right' :
                                            col.align === 'center' ? 'text-center' : 'text-left'
                                        } ${col.sortable !== false && onSort ? 'cursor-pointer hover:bg-gray-100 transition' : ''}`}
                                >
                                    <div className={`flex items-center gap-1 ${col.align === 'right' ? 'justify-end' :
                                            col.align === 'center' ? 'justify-center' : 'justify-start'
                                        }`}>
                                        {col.label}
                                        {col.sortable !== false && onSort && sortConfig && (
                                            sortConfig.key === col.key ? (
                                                sortConfig.direction === 'asc' ? (
                                                    <ArrowUp className="w-3 h-3" style={{ color: COLORS.primary }} />
                                                ) : (
                                                    <ArrowDown className="w-3 h-3" style={{ color: COLORS.primary }} />
                                                )
                                            ) : (
                                                <ArrowUpDown className="w-3 h-3 opacity-30" />
                                            )
                                        )}
                                    </div>
                                </th>
                            ))}
                            {actionButton && (
                                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Action
                                </th>
                            )}
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {organizedData.map((row, rowIndex) => {
                            // Determine if this is a child row
                            const isChildRow = row.parentRegionId && !row.isParent;

                            // Find parent region if this is a child
                            let parentRow = null;
                            if (isChildRow) {
                                parentRow = organizedData.find(r => r.regionId === row.parentRegionId && r.isParent);
                            }

                            // Skip child rows if parent is not expanded
                            if (isChildRow && parentRow && !expandedRows.has(parentRow.regionId)) {
                                return null;
                            }

                            const isExpanded = expandedRows.has(row.regionId);
                            const hasChildren = row.isParent && row.subRegions && row.subRegions.length > 0;

                            return (
                                <tr
                                    key={rowIndex}
                                    className={`hover:bg-gray-50 transition ${onRowClick ? 'cursor-pointer' : ''
                                        } ${isChildRow ? 'bg-gray-50' : ''}`}
                                    onClick={() => {
                                        if (onRowClick) {
                                            onRowClick(row);
                                        }
                                    }}
                                >
                                    {columns.map((col, colIndex) => (
                                        <td
                                            key={colIndex}
                                            className={`px-6 py-4 whitespace-nowrap text-sm ${col.bold ? 'font-medium text-gray-900' : 'text-gray-600'
                                                } ${col.align === 'right' ? 'text-right' :
                                                    col.align === 'center' ? 'text-center' : 'text-left'
                                                }`}
                                        >
                                            {colIndex === 0 ? (
                                                <div className={`flex items-center gap-2 ${isChildRow ? 'pl-8' : ''}`}>
                                                    {hasChildren && (
                                                        <button
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                toggleRow(row.regionId);
                                                            }}
                                                            className="p-1 hover:bg-gray-200 rounded transition"
                                                        >
                                                            {isExpanded ? (
                                                                <ChevronDown className="w-4 h-4" style={{ color: COLORS.primary }} />
                                                            ) : (
                                                                <ChevronRight className="w-4 h-4" style={{ color: COLORS.primary }} />
                                                            )}
                                                        </button>
                                                    )}
                                                    <span className={row.isParent ? 'font-bold' : ''}>
                                                        {col.render ? col.render(row[col.key], row) : row[col.key]}
                                                    </span>
                                                </div>
                                            ) : (
                                                col.render ? col.render(row[col.key], row) : row[col.key]
                                            )}
                                        </td>
                                    ))}
                                    {actionButton && (
                                        <td className="px-6 py-4 whitespace-nowrap text-center text-sm">
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    actionButton.onClick(row);
                                                }}
                                                className="font-medium hover:opacity-80 transition"
                                                style={{ color: COLORS.primary }}
                                            >
                                                {actionButton.label} →
                                            </button>
                                        </td>
                                    )}
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}