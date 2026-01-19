import React from 'react';
import { motion } from 'framer-motion';
import classNames from 'classnames';

const VedicButton = ({
    children,
    onClick,
    variant = 'primary', // primary, secondary, outline
    className,
    disabled = false,
    type = 'button',
    icon: Icon
}) => {
    const baseStyles = "relative inline-flex items-center justify-center px-8 py-3 overflow-hidden font-bold transition-all duration-300 rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-60 disabled:cursor-not-allowed uppercase tracking-wide text-sm";

    const variants = {
        primary: "bg-vedic-orange text-white hover:bg-orange-600 shadow-lg shadow-orange-200 focus:ring-orange-500",
        secondary: "bg-vedic-blue text-white hover:bg-blue-900 shadow-lg shadow-blue-200 focus:ring-blue-500",
        outline: "border-2 border-vedic-orange text-vedic-orange hover:bg-vedic-orange hover:text-white focus:ring-orange-500",
        ghost: "text-vedic-muted hover:text-vedic-orange bg-transparent"
    };

    return (
        <motion.button
            type={type}
            className={classNames(baseStyles, variants[variant], className)}
            onClick={onClick}
            disabled={disabled}
            whileTap={{ scale: 0.98 }}
        >
            <span className="relative flex items-center gap-2">
                {Icon && <Icon size={18} />}
                {children}
            </span>
        </motion.button>
    );
};

export default VedicButton;
