import React from 'react';
import { COLORS } from '../../constants/theme';

export default function Header() {
    return (
        <header className="bg-white shadow-sm border-b" style={{ borderColor: COLORS.border }}>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                <div className="flex items-center justify-between">
                    <div
                        className="flex flex-col items-center cursor-pointer"
                        onClick={() => window.open('http://10.101.0.165/', '_blank')}
                    >
                        <span className="-mb-1 text-[10px] text-black font-semibold">LG Electronics HVAC Service & Maintenance</span>
                        <h1 className="text-4xl font-bold" style={{ color: COLORS.primary }}>
                            Hi-M.Solutek
                        </h1>
                    </div>
                    <div className="flex items-center gap-4">
                        <span className="text-sm text-gray-600">
                            {new Date().toLocaleDateString('en-US', {
                                weekday: 'short',
                                year: 'numeric',
                                month: 'short',
                                day: 'numeric'
                            })}
                        </span>
                    </div>
                </div>
            </div>
        </header>
    );
}