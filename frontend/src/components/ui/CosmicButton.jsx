import React from 'react';
import { motion } from 'framer-motion';
import classNames from 'classnames';

const CosmicButton = ({
    children,
    onClick,
    variant = 'primary', // primary, secondary, outline, ghost
    className,
    disabled = false,
    type = 'button',
    icon: Icon
}) => {
    const baseStyles = "relative inline-flex items-center justify-center px-6 py-3 overflow-hidden font-medium transition-all duration-300 rounded-xl group focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-cosmic-black disabled:opacity-50 disabled:cursor-not-allowed";

    const variants = {
        primary: "bg-gradient-to-r from-nebula-purple to-purple-600 text-white shadow-lg shadow-purple-500/20 hover:shadow-purple-500/40 focus:ring-purple-500",
        secondary: "bg-white/10 text-white hover:bg-white/20 hover:text-starlight-gold backdrop-blur-sm border border-white/5 focus:ring-white/30",
        outline: "border border-purple-500/50 text-purple-300 hover:text-white hover:border-purple-400 hover:bg-purple-500/10 focus:ring-purple-500/50",
        ghost: "text-gray-400 hover:text-white hover:bg-white/5 focus:ring-white/20"
    };

    return (
        <motion.button
            type={type}
            className={classNames(baseStyles, variants[variant], className)}
            onClick={onClick}
            disabled={disabled}
            whileTap={{ scale: 0.98 }}
            whileHover={!disabled ? { scale: 1.02 } : {}}
        >
            {/* Shine Effect for Primary */}
            {variant === 'primary' && (
                <span className="absolute inset-0 w-full h-full -mt-1 rounded-lg opacity-30 bg-gradient-to-b from-transparent via-transparent to-black" />
            )}

            <span className="relative flex items-center gap-2">
                {Icon && <Icon size={18} />}
                {children}
            </span>
        </motion.button>
    );
};

export default CosmicButton;
