import React, { useState } from 'react';
import {
    AreaChart as RechartsAreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    Label
} from 'recharts';
import { COLORS, CHART_CONFIG } from '../../constants/theme';

export default function AreaChart({
    data,
    title,
    areas = [],
    height = 350,
    showLegend = true,
    valueFormatter = (v) => v,
    xAxisTitle = '',
    yAxisTitleLeft = '',
    yAxisTitleRight = '',
    yAxisFormatterLeft = (v) => v,
    yAxisFormatterRight = (v) => v
}) {

    const [activeKey, setActiveKey] = useState(null);

    const handleLegendClick = (key) => {
        setActiveKey(prev => prev === key ? null : key);
    };

    const renderLegend = ({ payload }) => (
        <div className="flex flex-wrap gap-3 justify-center mt-4">
            {payload.map((entry, index) => {

                const dim = activeKey && activeKey !== entry.dataKey;

                return (
                    <div
                        key={index}
                        onClick={() => handleLegendClick(entry.dataKey)}
                        className={`flex items-center gap-2 px-3 py-1 rounded-full cursor-pointer transition ${dim ? 'opacity-40 bg-gray-100' : 'hover:bg-gray-50'}`}
                        style={{ border: `1px solid ${entry.color}20` }}
                    >
                        <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: entry.color }}
                        />
                        <span className="text-sm font-medium text-gray-700">
                            {entry.value}
                        </span>
                    </div>
                );
            })}
        </div>
    );

    const CustomTooltip = ({ active, payload, label }) => {

        if (!active || !payload?.length) return null;

        return (
            <div className="bg-white px-4 py-3 rounded-lg shadow-lg border border-gray-200">
                <p className="text-sm font-semibold text-gray-800 mb-2">{label}</p>

                {payload.map((entry, index) => (
                    <div key={index} className="flex items-center gap-2 mb-1">
                        <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: entry.color }}
                        />
                        <span className="text-sm text-gray-600">
                            {entry.name}: {valueFormatter(entry.value, entry.dataKey)}
                        </span>
                    </div>
                ))}
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
                    <RechartsAreaChart
                        data={data}
                        margin={{ top: 20, right: 40, left: 10, bottom: 20 }}
                    >

                        <defs>
                            {areas.map((area, i) => (
                                <linearGradient
                                    key={area.dataKey}
                                    id={`color${area.dataKey}`}
                                    x1="0"
                                    y1="0"
                                    x2="0"
                                    y2="1"
                                >
                                    <stop
                                        offset="5%"
                                        stopColor={area.color || COLORS.chart[i]}
                                        stopOpacity={0.8}
                                    />
                                    <stop
                                        offset="95%"
                                        stopColor={area.color || COLORS.chart[i]}
                                        stopOpacity={0.1}
                                    />
                                </linearGradient>
                            ))}
                        </defs>

                        <CartesianGrid
                            strokeDasharray="3 3"
                            stroke={COLORS.border}
                        />

                        <XAxis
                            dataKey="name"
                            fontSize={12}
                            stroke={COLORS.text.secondary}
                            tickLine={false}
                            axisLine={{ stroke: COLORS.border }}
                        >
                            {xAxisTitle && (
                                <Label
                                    value={xAxisTitle}
                                    position="bottom"
                                    offset={1}
                                    style={{ fill: COLORS.text.secondary, fontSize: 12 }}
                                />
                            )}
                        </XAxis>

                        <YAxis
                            yAxisId="left"
                            fontSize={12}
                            stroke={COLORS.text.secondary}
                            tickLine={false}
                            axisLine={{ stroke: COLORS.border }}
                            tickFormatter={yAxisFormatterLeft}
                        >
                            {yAxisTitleLeft && (
                                <Label
                                    value={yAxisTitleLeft}
                                    angle={-90}
                                    position="insideLeft"
                                    style={{ textAnchor: 'middle', fill: COLORS.text.secondary }}
                                />
                            )}
                        </YAxis>

                        <YAxis
                            yAxisId="right"
                            orientation="right"
                            fontSize={12}
                            stroke={COLORS.text.secondary}
                            tickLine={false}
                            axisLine={{ stroke: COLORS.border }}
                            tickFormatter={yAxisFormatterRight}
                        >
                            {yAxisTitleRight && (
                                <Label
                                    value={yAxisTitleRight}
                                    angle={90}
                                    position="insideRight"
                                    style={{ textAnchor: 'middle', fill: COLORS.text.secondary }}
                                />
                            )}
                        </YAxis>

                        <Tooltip content={<CustomTooltip />} />

                        {showLegend && <Legend content={renderLegend} />}

                        {areas.map((area, i) => (

                            <Area
                                key={area.dataKey}
                                type={CHART_CONFIG.curveType}
                                dataKey={area.dataKey}
                                name={area.name}
                                stroke={area.color || COLORS.chart[i % COLORS.chart.length]}
                                fill={`url(#color${area.dataKey})`}
                                strokeWidth={2}
                                animationDuration={CHART_CONFIG.animationDuration}
                                yAxisId={area.yAxisId || 'left'}
                                opacity={activeKey && activeKey !== area.dataKey ? 0.25 : 1}
                            />

                        ))}

                    </RechartsAreaChart>
                </ResponsiveContainer>

            )}

        </div>
    );
}