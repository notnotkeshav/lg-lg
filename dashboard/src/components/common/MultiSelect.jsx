// src/components/common/MultiSelect.jsx
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { ChevronDown, Check, X } from 'lucide-react';
import { COLORS } from '../../constants/theme';

/**
 * MultiSelect dropdown with checkboxes.
 *
 * Props:
 *   options       — [{ value, label }]
 *   value         — string[] of selected values
 *   onChange      — (string[]) => void
 *   placeholder   — shown when nothing selected (default "All")
 *   allLabel      — label for the "select all" row (default "All")
 */
export default function MultiSelect({
    options = [],
    value = [],
    onChange,
    placeholder = 'All',
    allLabel = 'All',
    singleSelect = false,
}) {
    const [open, setOpen] = useState(false);
    const ref = useRef(null);

    // Close on outside click
    useEffect(() => {
        function onDown(e) {
            if (ref.current && !ref.current.contains(e.target)) setOpen(false);
        }
        if (open) document.addEventListener('mousedown', onDown);
        return () => document.removeEventListener('mousedown', onDown);
    }, [open]);

    const isAllSelected = value.length === 0 || value.length === options.length;

    // For singleSelect, an empty value means the first option is the default (e.g. 'Active').
    // Use this for display only — don't mutate the actual value prop.
    const displayValue = (singleSelect && value.length === 0 && options.length > 0)
        ? [options[0].value]
        : value;

    const toggle = useCallback((optValue) => {
        if (singleSelect) {
            // Single-select: clicking the active item clears; clicking another sets only that
            onChange(value.includes(optValue) ? [] : [optValue]);
        } else {
            if (value.includes(optValue)) {
                onChange(value.filter(v => v !== optValue));
            } else {
                onChange([...value, optValue]);
            }
        }
    }, [value, onChange, singleSelect]);

    const selectAll = () => onChange([]);
    const clearAll  = () => onChange([]);

    // Display label
    const displayLabel = () => {
        if (value.length === 0) return placeholder;
        if (value.length === options.length) return placeholder;
        if (value.length === 1) {
            const opt = options.find(o => o.value === value[0]);
            return opt?.label ?? value[0];
        }
        return `${value.length} selected`;
    };

    const hasSelection = value.length > 0 && value.length < options.length;

    return (
        <div className="relative w-full" ref={ref}>
            {/* Trigger */}
            <button
                type="button"
                onClick={() => setOpen(v => !v)}
                className="w-full flex items-center justify-between px-3 py-2 border rounded-md text-sm bg-white hover:bg-gray-50 transition"
                style={{ borderColor: hasSelection ? COLORS.primary : COLORS.border }}
            >
                <span
                    className="truncate"
                    style={{ color: hasSelection ? COLORS.primary : COLORS.text.secondary }}
                >
                    {displayLabel()}
                </span>
                <div className="flex items-center gap-1 ml-1 shrink-0">
                    {hasSelection && (
                        <span
                            className="text-xs font-semibold px-1.5 py-0.5 rounded-full"
                            style={{ backgroundColor: COLORS.primary, color: 'white', fontSize: 10 }}
                        >
                            {value.length}
                        </span>
                    )}
                    {hasSelection ? (
                        <X
                            className="w-3.5 h-3.5 cursor-pointer hover:opacity-70"
                            style={{ color: COLORS.primary }}
                            onClick={(e) => { e.stopPropagation(); clearAll(); }}
                        />
                    ) : (
                        <ChevronDown
                            className={`w-4 h-4 transition-transform ${open ? 'rotate-180' : ''}`}
                            style={{ color: COLORS.text.secondary }}
                        />
                    )}
                </div>
            </button>

            {/* Dropdown */}
            {open && (
                <div
                    className="absolute z-50 mt-1 w-full bg-white border rounded-lg shadow-lg overflow-hidden"
                    style={{ borderColor: COLORS.border, minWidth: 180 }}
                >
                    {/* Select all row — hidden in singleSelect mode */}
                    {!singleSelect && (
                        <button
                            type="button"
                            onClick={selectAll}
                            className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-gray-50 transition border-b"
                            style={{ borderColor: COLORS.border }}
                        >
                            <span
                                className="w-4 h-4 rounded border flex items-center justify-center shrink-0"
                                style={{
                                    borderColor: isAllSelected ? COLORS.primary : COLORS.border,
                                    backgroundColor: isAllSelected ? COLORS.primary : 'white',
                                }}
                            >
                                {isAllSelected && <Check className="w-3 h-3 text-white" strokeWidth={3} />}
                            </span>
                            <span className="font-medium" style={{ color: COLORS.text.primary }}>
                                {allLabel}
                            </span>
                        </button>
                    )}

                    {/* Options */}
                    <div className="max-h-52 overflow-y-auto">
                        {options.map(opt => {
                            const checked = displayValue.includes(opt.value);
                            return (
                                <button
                                    key={opt.value}
                                    type="button"
                                    onClick={() => toggle(opt.value)}
                                    className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-gray-50 transition"
                                >
                                    {singleSelect ? (
                                        /* Radio circle */
                                        <span
                                            className="w-4 h-4 rounded-full border-2 flex items-center justify-center shrink-0"
                                            style={{ borderColor: checked ? COLORS.primary : COLORS.border }}
                                        >
                                            {checked && (
                                                <span
                                                    className="w-2 h-2 rounded-full"
                                                    style={{ backgroundColor: COLORS.primary }}
                                                />
                                            )}
                                        </span>
                                    ) : (
                                        /* Checkbox */
                                        <span
                                            className="w-4 h-4 rounded border flex items-center justify-center shrink-0"
                                            style={{
                                                borderColor: checked ? COLORS.primary : COLORS.border,
                                                backgroundColor: checked ? COLORS.primary : 'white',
                                            }}
                                        >
                                            {checked && <Check className="w-3 h-3 text-white" strokeWidth={3} />}
                                        </span>
                                    )}
                                    <span className="text-left leading-tight" style={{ color: COLORS.text.primary }}>{opt.label}</span>
                                </button>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
}