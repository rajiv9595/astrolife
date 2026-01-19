import React, { forwardRef } from 'react';
import classNames from 'classnames';

const Input = forwardRef(({ label, error, className, id, icon: Icon, ...props }, ref) => {
    return (
        <div className="flex flex-col gap-1.5 w-full">
            {label && (
                <label htmlFor={id} className="text-sm font-bold text-vedic-text ml-1 tracking-wide uppercase text-[11px]">
                    {label}
                </label>
            )}
            <div className="relative">
                {Icon && (
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-vedic-muted">
                        <Icon size={18} />
                    </div>
                )}
                <input
                    ref={ref}
                    id={id}
                    className={classNames(
                        "w-full bg-white border border-stone-200 rounded-lg px-4 py-3 text-vedic-text placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-vedic-orange focus:border-transparent transition-all hover:border-stone-300 shadow-sm",
                        Icon && "pl-10",
                        error && "border-red-500 focus:ring-red-200",
                        className
                    )}
                    {...props}
                />
            </div>
            {error && (
                <span className="text-xs text-red-500 ml-1 mt-0.5 font-medium">{error}</span>
            )}
        </div>
    );
});

Input.displayName = "Input";

export default Input;
