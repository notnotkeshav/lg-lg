// src/contexts/FilterContext.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';

const STORAGE_KEY = 'crm_dashboard_filters';

// contractStatus is now an array — empty means "Active only" (handled in filterByContractStatus)
const DEFAULT_FILTERS = {};

function loadFilters() {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) return DEFAULT_FILTERS;
        const parsed = JSON.parse(raw);
        // Migrate legacy single-string contractStatus to array
        if (parsed.contractStatus && !Array.isArray(parsed.contractStatus)) {
            parsed.contractStatus = parsed.contractStatus === 'Total'
                ? ['Active', 'Expired']
                : [parsed.contractStatus];
        }
        return { ...DEFAULT_FILTERS, ...parsed };
    } catch {
        return DEFAULT_FILTERS;
    }
}

const FilterContext = createContext();

export function FilterProvider({ children }) {
    const [globalFilters, setGlobalFilters] = useState(loadFilters);

    useEffect(() => {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(globalFilters));
        } catch {
            // private browsing / quota
        }
    }, [globalFilters]);

    const updateFilters = (newFilters) => {
        setGlobalFilters(prev => ({ ...prev, ...newFilters }));
    };

    const resetFilters = () => {
        setGlobalFilters(DEFAULT_FILTERS);
    };

    return (
        <FilterContext.Provider value={{ globalFilters, updateFilters, resetFilters }}>
            {children}
        </FilterContext.Provider>
    );
}

export function useFilters() {
    const context = useContext(FilterContext);
    if (!context) throw new Error('useFilters must be used within FilterProvider');
    return context;
}