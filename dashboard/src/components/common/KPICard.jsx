import React from 'react';
import { COLORS } from '../../constants/theme';

export default function KPICard({ title, value, subtitle, icon: Icon, trend }) {
    return (
        <div className="bg-white p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow border border-gray-100">
            <div className="flex items-start justify-between">
                <div className="flex-1">
                    <p className="text-sm font-medium text-gray-500 mb-2">{title}</p>
                    <p className="text-3xl font-bold text-gray-900">{value}</p>
                    {subtitle && (
                        <p className="text-sm text-gray-600 mt-1">{subtitle}</p>
                    )}
                </div>
                {Icon && (
                    <div
                        className="p-3 rounded-lg"
                        style={{ backgroundColor: `${COLORS.primary}15` }}
                    >
                        <Icon className="w-6 h-6" style={{ color: COLORS.primary }} />
                    </div>
                )}
            </div>
            {trend && (
                <div className="mt-4 flex items-center text-sm">
                    <span className={trend.value >= 0 ? 'text-green-600' : 'text-red-600'}>
                        {trend.value >= 0 ? '↑' : '↓'} {Math.abs(trend.value)}%
                    </span>
                    <span className="text-gray-500 ml-2">{trend.label}</span>
                </div>
            )}
        </div>
    );
}