import React, { useState, useMemo } from 'react';
import {
    PieChart,
    Pie,
    Cell,
    ResponsiveContainer,
    Tooltip,
    Legend
} from 'recharts';
import { COLORS, CHART_CONFIG } from '../../constants/theme';

export default function DonutChart({
    data,
    title,
    onSegmentClick,
    valueFormatter,
    height = 350
}) {
    const [activeKey, setActiveKey] = useState(null);

    const totalValue = useMemo(
        () => data.reduce((sum, item) => sum + item.value, 0),
        [data]
    );

    const displayData = useMemo(() => {
        if (!activeKey) return data;
        return data.map(item =>
            item.name === activeKey ? item : { ...item, value: 0 }
        );
    }, [data, activeKey]);

    const handleLegendClick = (key) => {
        setActiveKey(prev => (prev === key ? null : key));
    };

    const renderCustomLabel = ({
        cx,
        cy,
        midAngle,
        innerRadius,
        outerRadius,
        percent
    }) => {
        if (percent < 0.03) return null;

        const RADIAN = Math.PI / 180;
        const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
        const x = cx + radius * Math.cos(-midAngle * RADIAN);
        const y = cy + radius * Math.sin(-midAngle * RADIAN);

        return (
            <text
                x={x}
                y={y}
                fill="white"
                textAnchor={x > cx ? 'start' : 'end'}
                dominantBaseline="central"
                fontSize="12"
                fontWeight="600"
            >
                {`${(percent * 100).toFixed(0)}%`}
            </text>
        );
    };

    const renderLegend = (props) => {
        const { payload } = props;

        return (
            <div className="flex flex-wrap gap-3 justify-center mt-4">
                {payload.map((entry, index) => {
                    const isDimmed =
                        activeKey && activeKey !== entry.value;

                    return (
                        <div
                            key={`legend-${index}`}
                            onClick={() =>
                                handleLegendClick(entry.value)
                            }
                            className={`flex items-center gap-2 px-3 py-1 rounded-full cursor-pointer transition ${isDimmed
                                    ? 'opacity-40 bg-gray-100'
                                    : 'hover:bg-gray-50'
                                }`}
                            style={{
                                border: `1px solid ${entry.color}20`
                            }}
                        >
                            <div
                                className="w-3 h-3 rounded-full"
                                style={{
                                    backgroundColor: entry.color
                                }}
                            />
                            <span className="text-sm font-medium text-gray-700">
                                {entry.value}
                            </span>
                        </div>
                    );
                })}
            </div>
        );
    };

    const CustomTooltip = ({ active, payload }) => {
        if (!active || !payload || !payload.length) return null;

        const item = payload[0];

        return (
            <div className="bg-white px-4 py-3 rounded-lg shadow-lg border border-gray-200">
                <p className="text-sm font-semibold text-gray-800 mb-1">
                    {item.name}
                </p>
                <p className="text-sm text-gray-600">
                    {valueFormatter
                        ? valueFormatter(item.value)
                        : item.value}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                    {((item.payload.value / totalValue) * 100).toFixed(1)}%
                </p>
            </div>
        );
    };

    return (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100 hover:shadow-md transition">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
                {title}
            </h3>

            {data.length === 0 ? (
                <div className="flex items-center justify-center h-64 text-gray-400">
                    No data available
                </div>
            ) : (
                <ResponsiveContainer width="100%" height={height}>
                    <PieChart>
                        <Pie
                            data={displayData}
                            cx="50%"
                            cy="45%"
                            labelLine={false}
                            label={renderCustomLabel}
                            innerRadius={
                                CHART_CONFIG.donut.innerRadius
                            }
                            outerRadius={
                                CHART_CONFIG.donut.outerRadius
                            }
                            paddingAngle={
                                CHART_CONFIG.donut.paddingAngle
                            }
                            dataKey="value"
                            onClick={onSegmentClick}
                            style={{
                                cursor: onSegmentClick
                                    ? 'pointer'
                                    : 'default'
                            }}
                            animationDuration={
                                CHART_CONFIG.animationDuration
                            }
                        >
                            {data.map((entry, index) => (
                                <Cell
                                    key={`cell-${index}`}
                                    fill={
                                        COLORS.chart[
                                        index %
                                        COLORS.chart.length
                                        ]
                                    }
                                    opacity={
                                        activeKey &&
                                            activeKey !== entry.name
                                            ? 0.25
                                            : 1
                                    }
                                />
                            ))}
                        </Pie>

                        <Tooltip content={<CustomTooltip />} />
                        <Legend content={renderLegend} />
                    </PieChart>
                </ResponsiveContainer>
            )}
        </div>
    );
}