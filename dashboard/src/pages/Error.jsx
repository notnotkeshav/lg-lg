// src/pages/ErrorPage.jsx
import { useRouteError, useNavigate, isRouteErrorResponse } from 'react-router-dom';
import { AlertTriangle, Home, RefreshCw, ChevronDown, ChevronUp, FileWarning } from 'lucide-react';
import { COLORS } from '../constants/theme';
import { useState } from 'react';

export default function ErrorPage() {
    const error = useRouteError();
    const navigate = useNavigate();
    const [showStack, setShowStack] = useState(false);

    let title   = 'Something went wrong';
    let message = 'An unexpected error occurred.';
    let stack   = null;

    if (isRouteErrorResponse(error)) {
        title   = `${error.status} — ${error.statusText}`;
        message = error.data?.message || error.statusText;
    } else if (error instanceof Error) {
        title   = error.name;
        message = error.message;
        stack   = error.stack;
    } else if (typeof error === 'string') {
        message = error;
    }

    return (
        <div
            className="min-h-[calc(100vh-120px)] flex items-center justify-center px-6 py-12"
            style={{ backgroundColor: COLORS.background }}
        >
            <div className="w-full max-w-3xl">

                {/* Hero section */}
                <div className="flex flex-col items-center text-center mb-10">
                    <div
                        className="w-20 h-20 rounded-2xl flex items-center justify-center mb-6"
                        style={{ backgroundColor: '#fef2f2' }}
                    >
                        <AlertTriangle className="w-10 h-10" style={{ color: '#ef4444' }} />
                    </div>

                    <p
                        className="text-xs font-bold uppercase tracking-widest mb-3"
                        style={{ color: '#ef4444' }}
                    >
                        Application Error
                    </p>

                    <h1
                        className="text-4xl font-bold mb-4"
                        style={{ color: COLORS.text.primary }}
                    >
                        Error: {title}
                    </h1>

                    <p
                        className="text-base leading-relaxed max-w-lg"
                        style={{ color: COLORS.text.secondary }}
                    >
                        Message: {message}
                    </p>
                </div>

                {/* Action buttons */}
                <div className="flex items-center justify-center gap-4 mb-10">
                    <button
                        onClick={() => navigate('/')}
                        className="flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold text-white transition hover:opacity-90 shadow-sm"
                        style={{ backgroundColor: COLORS.primary }}
                    >
                        <Home className="w-4 h-4" />
                        Go Home
                    </button>

                    <button
                        onClick={() => window.location.reload()}
                        className="flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold border transition hover:bg-white shadow-sm"
                        style={{
                            color: COLORS.text.secondary,
                            borderColor: COLORS.border,
                            backgroundColor: 'transparent',
                        }}
                    >
                        <RefreshCw className="w-4 h-4" />
                        Reload Page
                    </button>

                    <button
                        onClick={() => navigate(-1)}
                        className="flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold border transition hover:bg-white shadow-sm"
                        style={{
                            color: COLORS.text.secondary,
                            borderColor: COLORS.border,
                            backgroundColor: 'transparent',
                        }}
                    >
                        ← Go Back
                    </button>
                </div>

                {/* Stack trace card */}
                {stack && (
                    <div
                        className="rounded-2xl overflow-hidden border"
                        style={{ borderColor: COLORS.border }}
                    >
                        {/* Card header */}
                        <button
                            onClick={() => setShowStack(v => !v)}
                            className="w-full flex items-center justify-between px-6 py-4 bg-white transition hover:bg-gray-50"
                        >
                            <div className="flex items-center gap-3">
                                <div
                                    className="w-8 h-8 rounded-lg flex items-center justify-center"
                                    style={{ backgroundColor: '#fef2f2' }}
                                >
                                    <FileWarning className="w-4 h-4" style={{ color: '#ef4444' }} />
                                </div>
                                <div className="text-left">
                                    <p className="text-sm font-semibold" style={{ color: COLORS.text.primary }}>
                                        Stack Trace
                                    </p>
                                    <p className="text-xs" style={{ color: COLORS.text.secondary }}>
                                        Click to {showStack ? 'collapse' : 'expand'} full error details
                                    </p>
                                </div>
                            </div>
                            {showStack
                                ? <ChevronUp className="w-5 h-5" style={{ color: COLORS.text.secondary }} />
                                : <ChevronDown className="w-5 h-5" style={{ color: COLORS.text.secondary }} />
                            }
                        </button>

                        {/* Stack body */}
                        {showStack && (
                            <pre
                                className="text-xs leading-relaxed overflow-auto px-6 py-5"
                                style={{
                                    backgroundColor: '#0f172a',
                                    color: '#94a3b8',
                                    maxHeight: 320,
                                    fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
                                    borderTop: '1px solid #1e293b',
                                }}
                            >
                                <span style={{ color: '#f87171' }}>{title}: </span>
                                <span style={{ color: '#e2e8f0' }}>{message}{'\n\n'}</span>
                                {stack
                                    .split('\n')
                                    .slice(1)       // skip the first "Error: message" line — already shown above
                                    .join('\n')}
                            </pre>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}