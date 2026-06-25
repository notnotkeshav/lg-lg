import React from 'react';
import { COLORS } from '../../constants/theme';
import { Link } from 'react-router-dom';

export default function Footer() {
    return (
        <footer className="bg-white border-t mt-auto" style={{ borderColor: COLORS.border }}>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                <div className="flex items-center justify-between">
                    <p className="text-sm text-gray-500">
                        © {new Date().getFullYear()} Hi-M.Solutek. All rights reserved.
                    </p>
                    <Link to="https://extensionerp.com" target='_blank' className="text-sm text-gray-500">
                        Powered by Extension ERP
                    </Link>
                </div>
            </div>
        </footer>
    );
}