import React from 'react';
import { motion } from 'framer-motion';
import classNames from 'classnames';

const VedicCard = ({ children, className, hoverEffect = false, ...props }) => {
    return (
        <motion.div
            className={classNames(
                "relative overflow-hidden rounded-xl bg-white shadow-vedic border border-stone-100",
                className
            )}
            whileHover={hoverEffect ? { y: -5, boxShadow: "0 15px 30px rgba(0,0,0,0.1)" } : {}}
            transition={{ duration: 0.3 }}
            {...props}
        >
            {/* Decorative Top Border */}
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-vedic-gold via-vedic-orange to-vedic-gold opacity-50" />

            {/* Content */}
            <div className="relative z-10">
                {children}
            </div>
        </motion.div>
    );
};

export default VedicCard;
