import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, Sun } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import VedicButton from './VedicButton';

const Navbar = () => {
    const [isOpen, setIsOpen] = useState(false);
    const location = useLocation();
    const isAuth = localStorage.getItem('token');

    return (
        <>
            {/* Top Bar (Panchang Strip) - Hidden on mobile */}
            <div className="hidden md:flex justify-between items-center px-8 py-2 bg-vedic-blue text-white text-xs tracking-wider">
                <div>Talk to Astrologers: +91 98765 43210</div>
                <div className="flex gap-4">
                    <span>info@lifepath.com</span>
                    <span>Follow us on FB In Tw</span>
                </div>
            </div>

            {/* Main Navbar */}
            <nav className="sticky top-0 z-50 bg-white shadow-md border-b border-stone-100">
                <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">

                    {/* Logo */}
                    <Link to="/" className="flex items-center gap-3 group">
                        <div className="relative w-10 h-10 flex items-center justify-center bg-vedic-orange rounded-full text-white">
                            <Sun className="w-6 h-6 animate-spin-slow" />
                        </div>
                        <div className="flex flex-col">
                            <span className="text-2xl font-serif font-bold text-vedic-blue leading-none">LifePath</span>
                            <span className="text-[10px] text-vedic-gold font-bold tracking-[0.2em] uppercase">Vedic Wisdom</span>
                        </div>
                    </Link>

                    {/* Desktop Menu */}
                    <div className="hidden md:flex items-center gap-8">
                        <Link to="/" className="text-sm font-bold text-vedic-text hover:text-vedic-orange transition-colors uppercase tracking-wide">Home</Link>
                        <Link to="/about" className="text-sm font-bold text-vedic-text hover:text-vedic-orange transition-colors uppercase tracking-wide">About</Link>

                        <Link to="/services" className="text-sm font-bold text-vedic-text hover:text-vedic-orange transition-colors uppercase tracking-wide">
                            Services
                        </Link>

                        <Link to="/blog" className="text-sm font-bold text-vedic-text hover:text-vedic-orange transition-colors uppercase tracking-wide">Blog</Link>

                        {isAuth ? (
                            <div className="flex items-center gap-4">
                                <Link to="/dashboard">
                                    <VedicButton variant="primary" className="!py-2 !px-6 text-sm">
                                        Dashboard
                                    </VedicButton>
                                </Link>
                                <button
                                    onClick={() => {
                                        localStorage.removeItem('token');
                                        localStorage.removeItem('user');
                                        window.location.href = '/';
                                    }}
                                    className="text-sm font-bold text-vedic-muted hover:text-vedic-orange transition-colors uppercase tracking-wide"
                                >
                                    Logout
                                </button>
                            </div>
                        ) : (
                            <div className="flex items-center gap-4">
                                <Link to="/auth?mode=login" className="text-sm font-bold text-vedic-blue hover:text-vedic-orange transition-colors uppercase">
                                    Login
                                </Link>
                                <Link to="/auth?mode=signup">
                                    <VedicButton variant="primary" className="!py-2 !px-6 text-xs shadow-none">
                                        Chat Now
                                    </VedicButton>
                                </Link>
                            </div>
                        )}
                    </div>

                    {/* Mobile Menu Button */}
                    <button
                        className="md:hidden text-vedic-blue p-2"
                        onClick={() => setIsOpen(!isOpen)}
                    >
                        {isOpen ? <X /> : <Menu />}
                    </button>
                </div>

                {/* Mobile Menu */}
                <AnimatePresence>
                    {isOpen && (
                        <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="md:hidden bg-white border-t border-stone-100 shadow-lg"
                        >
                            <div className="flex flex-col p-6 gap-4">
                                <Link to="/" className="text-vedic-text font-bold">Home</Link>
                                <Link to="/about" className="text-vedic-text font-bold">About</Link>
                                <Link to="/services" className="text-vedic-text font-bold">Services</Link>
                                {!isAuth && (
                                    <>
                                        <Link to="/auth?mode=login" className="text-vedic-blue font-bold">Login</Link>
                                        <Link to="/auth?mode=signup" className="text-vedic-orange font-bold">Get Kundli</Link>
                                    </>
                                )}
                                {isAuth && (
                                    <>
                                        <Link to="/dashboard" className="text-vedic-orange font-bold">Dashboard</Link>
                                        <button
                                            onClick={() => {
                                                localStorage.removeItem('token');
                                                localStorage.removeItem('user');
                                                window.location.href = '/';
                                            }}
                                            className="text-left text-vedic-muted font-bold hover:text-vedic-orange transition-colors"
                                        >
                                            Logout
                                        </button>
                                    </>
                                )}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </nav >
        </>
    );
};

export default Navbar;
