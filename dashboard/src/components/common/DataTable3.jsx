// src/components/common/DataTable.jsx
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

    // universal row id resolver
    const getRowId = (row) => row.regionId || row.branchId || row.id;

    const toggleRow = (rowId) => {
        const newExpanded = new Set(expandedRows);

        if (newExpanded.has(rowId)) {
            newExpanded.delete(rowId);
        } else {
            newExpanded.add(rowId);
        }

        setExpandedRows(newExpanded);
    };

    // Organize data into parent-child structure
    const organizedData = React.useMemo(() => {

        const result = [];
        const processed = new Set();

        data.forEach(row => {

            const rowId = getRowId(row);

            // Skip if already processed as a child
            if (processed.has(rowId)) return;

            result.push(row);
            processed.add(rowId);

            // If this is a parent with sub-regions, add children
            if (row.isParent && row.subRegions) {

                row.subRegions.forEach(subRegionId => {

                    const subRegion = data.find(r =>
                        r.regionId === subRegionId ||
                        r.branchId === subRegionId
                    );

                    if (subRegion) {

                        const childId = getRowId(subRegion);

                        result.push({
                            ...subRegion,
                            isChild: true,
                            parentId: rowId
                        });

                        processed.add(childId);
                    }

                });

            }

        });

        return result;

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
                                    className={`px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider 
                                    ${col.align === 'right' ? 'text-right' :
                                            col.align === 'center' ? 'text-center' : 'text-left'
                                        } ${col.sortable !== false && onSort ? 'cursor-pointer hover:bg-gray-100 transition' : ''}`}
                                >

                                    <div className={`flex items-center gap-1 
                                    ${col.align === 'right' ? 'justify-end' :
                                            col.align === 'center' ? 'justify-center' : 'justify-start'
                                        }`}>

                                        {col.label}

                                        {col.sortable !== false && onSort && sortConfig && (

                                            sortConfig.key === col.key ?

                                                sortConfig.direction === 'asc'
                                                    ? <ArrowUp className="w-3 h-3" style={{ color: COLORS.primary }} />
                                                    : <ArrowDown className="w-3 h-3" style={{ color: COLORS.primary }} />

                                                :

                                                <ArrowUpDown className="w-3 h-3 opacity-30" />

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

                            const rowId = getRowId(row);

                            // Skip child rows if parent is not expanded
                            if (row.isChild && !expandedRows.has(row.parentId)) {
                                return null;
                            }

                            const isExpanded = expandedRows.has(rowId);
                            const hasChildren = row.isParent && row.subRegions && row.subRegions.length > 0;

                            return (

                                <tr
                                    key={rowId || rowIndex}
                                    className={`hover:bg-gray-50 transition 
                                    ${onRowClick && !row.isParent ? 'cursor-pointer' : ''}
                                    ${row.isChild ? 'bg-gray-50' : ''}`}
                                    onClick={() => {

                                        if (!row.isParent && onRowClick) {
                                            onRowClick(row);
                                        }

                                    }}
                                >

                                    {columns.map((col, colIndex) => (

                                        <td
                                            key={colIndex}
                                            className={`px-6 py-4 whitespace-nowrap text-sm 
                                            ${col.bold ? 'font-medium text-gray-900' : 'text-gray-600'}
                                            ${col.align === 'right' ? 'text-right' :
                                                    col.align === 'center' ? 'text-center' : 'text-left'
                                                }`}
                                        >

                                            {colIndex === 0 ? (

                                                <div className={`flex items-center gap-2 ${row.isChild ? 'pl-8' : ''}`}>

                                                    {hasChildren && (

                                                        <button
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                toggleRow(rowId);
                                                            }}
                                                            className="p-1 hover:bg-gray-200 rounded transition"
                                                        >

                                                            {isExpanded
                                                                ? <ChevronDown className="w-4 h-4" style={{ color: COLORS.primary }} />
                                                                : <ChevronRight className="w-4 h-4" style={{ color: COLORS.primary }} />
                                                            }

                                                        </button>

                                                    )}

                                                    <span className={row.isParent ? 'font-bold' : ''}>
                                                        {col.render ? col.render(row[col.key], row) : row[col.key]}
                                                    </span>

                                                </div>

                                            ) : (

                                                col.render
                                                    ? col.render(row[col.key], row)
                                                    : row[col.key]
                                            )}
                                        </td>
                                    ))}
                                    {actionButton && (
                                        <td className="px-6 py-4 whitespace-nowrap text-center text-sm">
                                            {!row.isParent && (
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
                                            )}
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