import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import VedicCard from '../components/ui/VedicCard';
import LoginForm from '../components/auth/LoginForm';
import SignupForm from '../components/auth/SignupForm';
import Navbar from '../components/ui/Navbar';
import { Sun } from 'lucide-react';

const AuthPage = () => {
    const [searchParams] = useSearchParams();
    const initialMode = searchParams.get('mode') === 'signup' ? 'signup' : 'login';
    const [mode, setMode] = useState(initialMode);

    return (
        <div className="min-h-screen flex bg-white">
            {/* Left Side - Visual / Brand */}
            <div className="hidden lg:flex lg:w-1/2 relative bg-vedic-blue overflow-hidden">
                <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1532968961962-8a0cb3a2d4f5?q=80&w=2070&auto=format&fit=crop')] bg-cover bg-center opacity-40"></div>
                <div className="absolute inset-0 bg-gradient-to-t from-vedic-blue via-transparent to-transparent"></div>

                <div className="relative z-10 flex flex-col justify-between p-12 w-full h-full text-white">
                    <div className="flex items-center gap-3">
                        <Sun className="text-vedic-orange w-8 h-8" />
                        <span className="text-2xl font-serif font-bold tracking-wide">LifePath</span>
                    </div>

                    <div className="max-w-md">
                        <h1 className="text-4xl font-serif font-bold mb-4 leading-tight">
                            Unlock the Wisdom of the Stars
                        </h1>
                        <p className="text-stone-300 text-lg leading-relaxed">
                            Discover your karmic path, understand your strengths, and navigate life with ancient Vedic precision.
                        </p>
                    </div>

                    <div className="flex gap-2">
                        <div className="w-2 h-2 rounded-full bg-vedic-orange"></div>
                        <div className="w-2 h-2 rounded-full bg-white/30"></div>
                        <div className="w-2 h-2 rounded-full bg-white/30"></div>
                    </div>
                </div>
            </div>

            {/* Right Side - Auth Form */}
            <div className="w-full lg:w-1/2 flex flex-col relative overflow-y-auto">
                <div className="absolute top-0 right-0 p-6">
                    <button onClick={() => window.history.back()} className="text-stone-400 hover:text-stone-600 font-bold text-sm">
                        &larr; Back to Home
                    </button>
                </div>

                <div className="flex-1 flex flex-col justify-center px-8 sm:px-16 lg:px-24 py-12">
                    <div className="mb-10 text-center lg:text-left">
                        <h2 className="text-3xl font-serif font-bold text-vedic-blue mb-2">
                            {mode === 'login' ? 'Welcome Back' : 'Begin Your Journey'}
                        </h2>
                        <p className="text-stone-500">
                            {mode === 'login'
                                ? 'Sign in to access your detailed charts.'
                                : 'Create an account to verify your predictions.'}
                        </p>
                    </div>

                    <div className="bg-white rounded-xl">
                        <AnimatePresence mode="wait">
                            <motion.div
                                key={mode}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                transition={{ duration: 0.2 }}
                            >
                                {mode === 'login' ? <LoginForm /> : <SignupForm />}
                            </motion.div>
                        </AnimatePresence>
                    </div>

                    <div className="mt-8 text-center border-t border-stone-100 pt-6">
                        {mode === 'login' ? (
                            <p className="text-stone-500 text-sm">
                                Don't have an account?{' '}
                                <button
                                    onClick={() => setMode('signup')}
                                    className="text-vedic-orange font-bold hover:underline"
                                >
                                    Register Free
                                </button>
                            </p>
                        ) : (
                            <p className="text-stone-500 text-sm">
                                Already have an account?{' '}
                                <button
                                    onClick={() => setMode('login')}
                                    className="text-vedic-orange font-bold hover:underline"
                                >
                                    Login Here
                                </button>
                            </p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AuthPage;
