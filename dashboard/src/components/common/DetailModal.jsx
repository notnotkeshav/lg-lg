import React from 'react';
import { COLORS } from '../../constants/theme';

export default function DetailModal({ show, title, data, onClose }) {
    if (!show || !data || data.length === 0) return null;

    const columns = Object.keys(data[0]);

    return (
        <div
            className="fixed inset-0 flex items-center justify-center z-50 p-4 backdrop-blur-sm"
            style={{ backgroundColor: 'rgba(255,255,255,0.25)' }}
            onClick={onClose}
        >
            <div
                className="bg-white rounded-xl max-w-7xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div
                    className="px-6 py-4 border-b border-gray-200 flex items-center justify-between flex-shrink-0"
                    style={{ backgroundColor: `${COLORS.primary}05` }}
                >
                    <h2 className="text-2xl font-bold text-gray-800">{title}</h2>

                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600 transition p-2 hover:bg-gray-100 rounded-full"
                    >
                        <svg
                            className="w-6 h-6"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M6 18L18 6M6 6l12 12"
                            />
                        </svg>
                    </button>
                </div>

                {/* Scrollable Table Area */}
                <div className="flex-1 overflow-auto">
                    <div className="min-w-full inline-block align-middle">
                        <div className="overflow-x-auto">
                            <table className="min-w-full table-auto divide-y divide-gray-200">

                                <thead className="bg-white sticky top-0 z-20 shadow-sm">
                                    <tr>
                                        {columns.map((col, index) => (
                                            <th
                                                key={index}
                                                className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap"
                                            >
                                                {col.replace(/_/g, ' ')}
                                            </th>
                                        ))}
                                    </tr>
                                </thead>

                                <tbody className="bg-white divide-y divide-gray-200">
                                    {data.map((row, rowIndex) => (
                                        <tr
                                            key={rowIndex}
                                            className="hover:bg-gray-50 transition"
                                        >
                                            {columns.map((col, colIndex) => (
                                                <td
                                                    key={colIndex}
                                                    className="px-4 py-3 whitespace-nowrap text-sm text-gray-900"
                                                >
                                                    {row[col] ?? '-'}
                                                </td>
                                            ))}
                                        </tr>
                                    ))}
                                </tbody>

                            </table>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex items-center justify-between flex-shrink-0">
                    <span className="text-sm text-gray-600">
                        Showing {data.length} record{data.length !== 1 ? 's' : ''}
                    </span>

                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-white rounded-md hover:opacity-90 transition font-medium"
                        style={{ backgroundColor: COLORS.primary }}
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
}