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
        <div className="min-h-screen bg-vedic-cream relative flex flex-col">
            <Navbar />

            <div className="flex-1 py-16 px-6 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')]">
                <div className="max-w-md mx-auto">
                    <div className="text-center mb-8">
                        <h2 className="text-3xl font-serif font-bold text-vedic-blue mb-2">
                            {mode === 'login' ? 'Member Login' : 'Create Account'}
                        </h2>
                        <div className="w-12 h-1 bg-vedic-orange mx-auto"></div>
                    </div>

                    <VedicCard className="p-8 md:p-10 shadow-xl">
                        <AnimatePresence mode="wait">
                            <motion.div
                                key={mode}
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                transition={{ duration: 0.2 }}
                            >
                                {mode === 'login' ? <LoginForm /> : <SignupForm />}
                            </motion.div>
                        </AnimatePresence>
                    </VedicCard>

                    <div className="mt-8 text-center bg-white p-4 rounded-lg shadow-sm border border-stone-100">
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
