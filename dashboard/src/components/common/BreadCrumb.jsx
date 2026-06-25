import React from 'react';
import { ChevronRight, Home } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { COLORS } from '../../constants/theme';

export default function Breadcrumb({ items }) {
    const navigate = useNavigate();

    return (
        <nav className="flex justify-end w-full text-sm mb-6">
            <div className="flex items-center space-x-2">

                <button
                    onClick={() => navigate('/')}
                    className="flex items-center gap-1 text-gray-600 hover:text-gray-900 transition"
                >
                    <Home className="w-4 h-4" />
                    <span>All India</span>
                </button>

                {items.map((item, index) => (
                    <React.Fragment key={index}>
                        <ChevronRight className="w-4 h-4 text-gray-400" />

                        {item.href ? (
                            <button
                                onClick={() => navigate(item.href)}
                                className="text-gray-600 hover:text-gray-900 transition"
                            >
                                {item.label}
                            </button>
                        ) : (
                            <span
                                className="font-semibold"
                                style={{ color: COLORS.text.primary }}
                            >
                                {item.label}
                            </span>
                        )}
                    </React.Fragment>
                ))}
            </div>
        </nav>
    );
}