// src/hooks/useFilterOptions.js
import { useFrappeGetDocList } from "frappe-react-sdk";

/**
 * Hook to fetch all available filter options
 */
export function useFilterOptions(additionalData = {}) {
    /**
     * Fetch Industry Tree
     */
    const {
        data: industryTree,
        isLoading: industriesLoading,
        error: industriesError
    } = useFrappeGetDocList("CRM Industry", {
        fields: ["name", "industry", "parent_vertical"],
        limit: 0,
        orderBy: {
            field: "industry",
            order: "asc",
        },
    });

    /**
     * Fetch Deal Types
    */
    const filteredDealTypeData = ["AMC Renewal", "Warranty AMC Conversion", "Lost AMC Conversion", "Lost Warranty Conversion",];

    /**
     * Fetch Deal Statuses
     */
    const {
        data: dealsData,
        isLoading: statusesLoading,
        error: statusesError
    } = useFrappeGetDocList("CRM Deal", {
        fields: ["status"],
        limit: 1000,
    });

    // Get unique verticals (where industry === parent_vertical)
    const verticals = industryTree
        ? [...new Set(industryTree
            .filter(item => item.parent_vertical && item.industry === item.parent_vertical)
            .map(v => v.parent_vertical))]
            .sort()
            .map(v => ({ value: v, label: v }))
        : [];

    const statuses = dealsData
        ? [...new Set(dealsData.map(d => d.status).filter(Boolean))]
            .sort()
            .map(status => ({ value: status, label: status }))
        : [];

    const dealTypes = filteredDealTypeData.length > 0
        ? filteredDealTypeData.map(d => ({ value: d, label: d }))
        : [];

    const isLoading = industriesLoading || statusesLoading;
    const error = industriesError || statusesError;

    const branches = additionalData.branches || [];

    return {
        verticals,
        dealTypes,
        statuses,
        branches: branches.map(b => ({ value: b.branchId, label: b.branchName })),
        isLoading,
        error,
    };
}