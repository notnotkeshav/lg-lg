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
import { COLORS } from '../../constants/theme';

const formatCurrencyCompact = (value) =>
    new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        notation: 'compact',
        maximumFractionDigits: 1
    }).format(value);

const formatNumberCompact = (value) =>
    new Intl.NumberFormat('en-IN', {
        notation: 'compact',
        maximumFractionDigits: 1
    }).format(value);

export default function StackedBarChart({
    data,
    title,
    stacks = [],
    onBarClick,
    valueFormatter = (v) => v,
    yAxisFormatter = (v) => v,
    height = 400,
    xAxisLabel = "Region",
    yAxisLabel = "Value"
}) {
    const [activeKey, setActiveKey] = useState(null);

    const handleLegendClick = (key) => {
        setActiveKey(prev => prev === key ? null : key);
    };

    const displayData = useMemo(() => {
        return data.map(row => {
            const filtered = { ...row };
            let total = 0;
            stacks.forEach(s => {
                const val = activeKey && s.dataKey !== activeKey ? 0 : (row[s.dataKey] || 0);
                filtered[s.dataKey] = val;
                total += val;
            });
            filtered.__total = total;
            return filtered;
        });
    }, [data, activeKey, stacks]);

    const renderLegend = () => (
        <div className="flex flex-wrap gap-3 justify-center mt-4">
            {stacks.map((stack, i) => {
                const dim = activeKey && activeKey !== stack.dataKey;
                return (
                    <div
                        key={i}
                        onClick={() => handleLegendClick(stack.dataKey)}
                        className={`flex items-center gap-2 px-3 py-1 rounded-full cursor-pointer transition ${
                            dim ? 'opacity-40 bg-gray-100' : 'hover:bg-gray-50'
                        }`}
                        style={{ border: `1px solid ${stack.color}30` }}
                    >
                        <div className="w-3 h-3 rounded-full" style={{ background: stack.color }} />
                        <span className="text-sm font-medium text-gray-700">{stack.name}</span>
                    </div>
                );
            })}
        </div>
    );

    const renderXAxisTick = ({ x, y, payload }) => (
        <g transform={`translate(${x},${y + 10})`}>
            <text
                transform="rotate(-35)"
                textAnchor="end"
                fill={COLORS.text.secondary}
                fontSize={12}
            >
                {payload.value}
            </text>
        </g>
    );

    // Only renders on the topmost non-zero stack for each bar — shows the full total.
    // Using a factory so each Bar knows its own dataKey without closure issues.
    const makeTotalLabel = (stackDataKey) => (props) => {
        const { x, y, width, index } = props;
        const entry = displayData[index];
        if (!entry) return null;

        const topKey = stacks.slice().reverse().find(s => entry[s.dataKey] > 0)?.dataKey;
        if (topKey !== stackDataKey) return null;

        const total = entry.__total;
        if (!total) return null;

        return (
            <text
                x={x + width / 2}
                y={y - 5}
                textAnchor="middle"
                fill={COLORS.text.secondary}
                fontSize={11}
                fontWeight={500}
            >
                {valueFormatter(total)}
            </text>
        );
    };

    const grandTotal = useMemo(() =>
        data.reduce((sum, row) =>
            sum + stacks.reduce((s2, st) => s2 + (row[st.dataKey] || 0), 0), 0),
    [data, stacks]);

    return (
        <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-baseline justify-between mb-4 gap-4">
                <h3 className="text-lg font-semibold" style={{ color: COLORS.text.primary }}>
                    {title}
                </h3>
                {grandTotal > 0 && (
                    <span className="text-sm font-semibold shrink-0" style={{ color: COLORS.text.secondary }}>
                        Total: {valueFormatter(grandTotal)}
                    </span>
                )}
            </div>

            <ResponsiveContainer width="100%" height={height}>
                <BarChart
                    data={displayData}
                    margin={{ top: 28, right: 30, left: 20, bottom: 75 }}
                    barCategoryGap="25%"
                >
                    <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />

                    <XAxis
                        dataKey="name"
                        interval={0}
                        tick={renderXAxisTick}
                        label={{ value: xAxisLabel, position: "insideBottom", offset: -50 }}
                    />

                    <YAxis
                        tick={{ fill: COLORS.text.secondary }}
                        tickFormatter={yAxisFormatter}
                        label={{ value: yAxisLabel, angle: -90, position: "insideLeft", offset: -10 }}
                    />

                    <Tooltip
                        // Hide the __total row from tooltip
                        formatter={(v, name) => {
                            if (name === '__total') return null;
                            return valueFormatter ? valueFormatter(v) : v;
                        }}
                        contentStyle={{
                            backgroundColor: "white",
                            border: `1px solid ${COLORS.border}`,
                            borderRadius: 8
                        }}
                    />

                    {stacks.map((stack) => (
                        <Bar
                            key={stack.dataKey}
                            dataKey={stack.dataKey}
                            stackId="a"
                            fill={stack.color}
                            name={stack.name}
                            barSize={32}
                            onClick={(d) => onBarClick?.({ ...d, stackKey: stack.dataKey })}
                            cursor="pointer"
                        >
                            {displayData.map((entry, index) => {
                                const isTop = stacks
                                    .slice()
                                    .reverse()
                                    .find(s => entry[s.dataKey] > 0)?.dataKey === stack.dataKey;

                                const isBottom = stacks
                                    .find(s => entry[s.dataKey] > 0)?.dataKey === stack.dataKey;

                                return (
                                    <Cell
                                        key={index}
                                        radius={[
                                            isTop ? 8 : 0,
                                            isTop ? 8 : 0,
                                            isBottom ? 8 : 0,
                                            isBottom ? 8 : 0,
                                        ]}
                                    />
                                );
                            })}

                            <LabelList content={makeTotalLabel(stack.dataKey)} />
                        </Bar>
                    ))}
                </BarChart>
            </ResponsiveContainer>

            {renderLegend()}
        </div>
    );
}

export { formatCurrencyCompact, formatNumberCompact };