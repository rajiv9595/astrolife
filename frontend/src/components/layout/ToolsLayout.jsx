import React from 'react';
import { Link, Outlet } from 'react-router-dom';
import Navbar from '../ui/Navbar';
import { ChevronLeft } from 'lucide-react';
import VedicButton from '../ui/VedicButton';

const ToolsLayout = () => {
    return (
        <div className="min-h-screen bg-vedic-cream flex flex-col">
            <Navbar />
            <div className="max-w-7xl mx-auto w-full pt-6 px-4 sm:px-6">

                {/* Back Button Area */}
                <div className="mb-6">
                    <Link to="/services">
                        <button className="flex items-center gap-2 text-stone-600 hover:text-vedic-orange transition-colors font-bold text-sm group">
                            <div className="p-1 rounded-full bg-white border border-stone-200 group-hover:border-vedic-orange transition-colors">
                                <ChevronLeft size={20} />
                            </div>
                            <span>Back to Tools</span>
                        </button>
                    </Link>
                </div>

                {/* Main Content Area */}
                <main className="flex-1 pb-20 overflow-x-hidden">
                    <Outlet />
                </main>
            </div>
        </div>
    );
};

export default ToolsLayout;
