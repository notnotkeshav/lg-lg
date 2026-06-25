// Hi-M Solutek & LG Brand Colors
export const COLORS = {
    // Primary Brand Colors
    primary: '#E4003B',      // LG Red
    secondary: '#A50034',    // Dark Red
    accent: '#FF6B9D',       // Pink accent

    // Hi-M Solutek Colors
    solutek: {
        blue: '#003DA5',       // Deep Blue
        lightBlue: '#0066CC',  // Light Blue
        gray: '#6B7280',       // Neutral Gray
    },

    // Chart Colors - Vibrant & Professional
    chart: [
        '#E4003B',  // LG Red
        '#003DA5',  // Solutek Blue
        '#00C49F',  // Teal
        '#FFBB28',  // Amber
        '#0066CC',  // Light Blue
        '#FF8042',  // Orange
        '#8884D8',  // Purple
        '#82CA9D',  // Green
        '#FFC658',  // Yellow
        '#FF6B9D',  // Pink
        '#A50034',  // Dark Red
        '#6B7280',  // Gray
    ],

    // Status Colors
    status: {
        success: '#10B981',
        warning: '#F59E0B',
        error: '#EF4444',
        info: '#3B82F6',
    },

    // UI Colors
    background: '#F9FAFB',
    surface: '#FFFFFF',
    border: '#E5E7EB',
    text: {
        primary: '#111827',
        secondary: '#6B7280',
        disabled: '#9CA3AF',
    },
};

export const CHART_CONFIG = {
    // Recharts stroke width for smooth lines
    strokeWidth: 3,

    // Curve type for smooth lines
    curveType: 'monotone',

    // Bar radius for rounded corners
    barRadius: [8, 8, 0, 0],

    // Donut chart config
    donut: {
        innerRadius: '40%',
        outerRadius: '80%',
        paddingAngle: 2,
    },

    // Animation
    animationDuration: 800,
    animationEasing: 'ease-in-out',
};