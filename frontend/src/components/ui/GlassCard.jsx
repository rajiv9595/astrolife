import React from 'react';
import { motion } from 'framer-motion';
import classNames from 'classnames';

const GlassCard = ({ children, className, hoverEffect = false, ...props }) => {
    return (
        <motion.div
            className={classNames(
                "relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md shadow-xl",
                className
            )}
            whileHover={hoverEffect ? { scale: 1.01, boxShadow: "0 20px 25px -5px rgba(124, 58, 237, 0.1), 0 8px 10px -6px rgba(124, 58, 237, 0.1)" } : {}}
            transition={{ duration: 0.3 }}
            {...props}
        >
            {/* Subtle Gradient Overlay */}
            <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent pointer-events-none" />

            {/* Content */}
            <div className="relative z-10">
                {children}
            </div>
        </motion.div>
    );
};

export default GlassCard;
