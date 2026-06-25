import React, { useState, useMemo } from 'react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Cell,
    LabelList,
} from 'recharts';
import { COLORS, CHART_CONFIG } from '../../constants/theme';

// Shorten long deal-type labels to fit the x-axis without excessive rotation
const LABEL_ALIASES = {
    'AMC Renewal':              'AMC',
    'Warranty Conversion':      'Warranty',
    'Lost AMC Conversion':      'Lost AMC',
    'Lost Warranty Conversion': 'Lost Warranty',
};

function shortenLabel(label) {
    return LABEL_ALIASES[label] ?? (label.length > 14 ? label.slice(0, 12) + '…' : label);
}

export default function RoundedBarChart({
    data,
    title,
    bars = [],
    onBarClick,
    yAxisFormatter = (v) => v,
    xAxisLabel = '',
    yAxisLabel = '',
    height = 350,
}) {
    // Active name mirrors the same pattern as StackedBarChart's activeKey,
    // but here we filter rows instead of columns.
    const [activeName, setActiveName] = useState(null);

    const handleLegendClick = (name) => {
        setActiveName(prev => prev === name ? null : name);
    };

    // When a legend item is selected, dim all other rows
    const displayData = useMemo(() => {
        if (!activeName) return data;
        return data.map(row => ({
            ...row,
            // zero out the value so the bar disappears; keep color for Cell
            ...(row.name !== activeName ? { value: 0 } : {}),
        }));
    }, [data, activeName]);

    // Build legend entries from the data rows (each row is its own "series")
    const legendItems = useMemo(() => data.map(row => ({
        name:  row.name,
        color: row.color ?? (bars[0]?.color ?? COLORS.primary),
    })), [data, bars]);

    const renderLegend = () => (
        <div className="flex flex-wrap gap-3 justify-center mt-4">
            {legendItems.map((item, i) => {
                const dim = activeName && activeName !== item.name;
                return (
                    <div
                        key={i}
                        onClick={() => handleLegendClick(item.name)}
                        className={`flex items-center gap-2 px-3 py-1 rounded-full cursor-pointer transition ${
                            dim ? 'opacity-40 bg-gray-100' : 'hover:bg-gray-50'
                        }`}
                        style={{ border: `1px solid ${item.color}30` }}
                    >
                        <div className="w-3 h-3 rounded-full" style={{ background: item.color }} />
                        <span className="text-sm font-medium text-gray-700">{item.name}</span>
                    </div>
                );
            })}
        </div>
    );

    const renderXAxisTick = ({ x, y, payload }) => (
        <g transform={`translate(${x},${y + 8})`}>
            <text
                transform="rotate(-30)"
                textAnchor="end"
                fill={COLORS.text.secondary}
                fontSize={12}
            >
                {shortenLabel(payload.value)}
            </text>
        </g>
    );

    const CustomTooltip = ({ active, payload, label }) => {
        if (!active || !payload?.length) return null;
        const barCfg = bars.find(b => b.dataKey === payload[0]?.dataKey);
        return (
            <div className="bg-white px-4 py-3 rounded-lg shadow-lg border border-gray-200">
                <p className="text-sm font-semibold text-gray-800 mb-2">{label}</p>
                {payload.map((entry, index) => (
                    <div key={index} className="flex items-center gap-2 mb-1">
                        <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: entry.payload?.color || entry.color }}
                        />
                        <span className="text-sm text-gray-600">
                            {entry.name}:{' '}
                            {barCfg?.formatter
                                ? barCfg.formatter(entry.value)
                                : entry.value}
                        </span>
                    </div>
                ))}
            </div>
        );
    };

    const renderLabel = (barConfig) => (props) => {
        const { x, y, width, value } = props;
        if (!value) return null;
        const formatted = barConfig.formatter ? barConfig.formatter(value) : value;
        return (
            <text
                x={x + width / 2}
                y={y - 5}
                textAnchor="middle"
                fill={COLORS.text.secondary}
                fontSize={11}
                fontWeight={500}
            >
                {formatted}
            </text>
        );
    };

    const grandTotal = useMemo(() =>
        data.reduce((sum, row) =>
            sum + bars.reduce((s2, b) => s2 + (row[b.dataKey] || 0), 0), 0),
    [data, bars]);

    return (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100 hover:shadow-md transition">
            <div className="flex items-baseline justify-between mb-4 gap-4">
                <h3 className="text-lg font-semibold" style={{ color: COLORS.text.primary }}>
                    {title}
                </h3>
                {grandTotal > 0 && (
                    <span className="text-sm font-semibold shrink-0" style={{ color: COLORS.text.secondary }}>
                        Total: {bars[0]?.formatter ? bars[0].formatter(grandTotal) : grandTotal}
                    </span>
                )}
            </div>

            {!data?.length ? (
                <div className="flex items-center justify-center h-64 text-gray-400">
                    No data available
                </div>
            ) : (
                <>
                    <ResponsiveContainer width="100%" height={height}>
                        <BarChart
                            data={displayData}
                            margin={{ top: 28, right: 30, left: 20, bottom: 80 }}
                            barCategoryGap="30%"
                        >
                            <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />

                            <XAxis
                                dataKey="name"
                                interval={0}
                                tick={renderXAxisTick}
                                label={xAxisLabel
                                    ? { value: xAxisLabel, position: 'insideBottom', offset: -30 }
                                    : undefined}
                            />

                            <YAxis
                                yAxisId="left"
                                tick={{ fill: COLORS.text.secondary, fontSize: 12 }}
                                tickFormatter={yAxisFormatter}
                                label={yAxisLabel
                                    ? { value: yAxisLabel, angle: -90, position: 'insideLeft', offset: 10 }
                                    : undefined}
                            />

                            <Tooltip content={<CustomTooltip />} />

                            {bars.map((bar, index) => (
                                <Bar
                                    key={bar.dataKey}
                                    dataKey={bar.dataKey}
                                    name={bar.name}
                                    fill={bar.color || COLORS.chart?.[index % (COLORS.chart?.length || 1)] || '#6366f1'}
                                    radius={CHART_CONFIG?.barRadius ?? [6, 6, 0, 0]}
                                    onClick={onBarClick}
                                    style={{ cursor: onBarClick ? 'pointer' : 'default' }}
                                    animationDuration={CHART_CONFIG?.animationDuration ?? 600}
                                    yAxisId={bar.yAxisId || 'left'}
                                    maxBarSize={64}
                                >
                                    {displayData.map((entry, i) => (
                                        <Cell
                                            key={i}
                                            fill={entry.color || bar.color || COLORS.chart?.[index % (COLORS.chart?.length || 1)]}
                                            opacity={activeName && activeName !== entry.name ? 0.15 : 1}
                                        />
                                    ))}

                                    <LabelList content={renderLabel(bar)} />
                                </Bar>
                            ))}
                        </BarChart>
                    </ResponsiveContainer>

                    {renderLegend()}
                </>
            )}
        </div>
    );
}