import React from 'react';
import { Skull, AlertOctagon, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';

const AdvancedDoshasCard = ({ doshas }) => {
    if (!doshas) return null;

    const kalaSarpa = doshas.kala_sarpa_dosha || {};
    const pitru = doshas.pitru_dosha || {};

    const renderDosha = (title, data, IconComponent, colorTheme) => {
        const isActive = data.has_dosha;
        
        return (
            <div className={`p-5 rounded-xl border ${isActive ? `border-${colorTheme}-200 bg-${colorTheme}-50/30` : 'border-emerald-100 bg-emerald-50/20'} transition-colors`}>
                <div className="flex items-start justify-between gap-4">
                    <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${isActive ? `bg-${colorTheme}-100 text-${colorTheme}-600` : 'bg-emerald-100 text-emerald-600'}`}>
                            {isActive ? <IconComponent size={20} /> : <CheckCircle2 size={20} />}
                        </div>
                        <div>
                            <h3 className={`font-serif font-bold text-lg ${isActive ? `text-${colorTheme}-900` : 'text-emerald-900'}`}>{title}</h3>
                            <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full ${isActive ? `bg-${colorTheme}-200 text-${colorTheme}-800` : 'bg-emerald-200 text-emerald-800'}`}>
                                {data.verdict}
                            </span>
                        </div>
                    </div>
                </div>
                
                <p className={`mt-3 text-sm leading-relaxed ${isActive ? `text-${colorTheme}-800` : 'text-emerald-800/80'}`}>
                    {data.details}
                </p>

                {isActive && data.reasons && data.reasons.length > 0 && (
                    <div className={`mt-3 pt-3 border-t border-${colorTheme}-200/50 space-y-1.5`}>
                        {data.reasons.map((r, idx) => (
                            <div key={idx} className={`flex items-start gap-1.5 text-xs text-${colorTheme}-700`}>
                                <span className="font-bold mt-0.5">•</span>
                                <span>{r}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        );
    };

    // If both are inactive, we might just show a consolidated "All Clear" or show the boxes.
    // Let's show the boxes so the user knows we checked them.

    return (
        <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full border border-stone-200 rounded-2xl p-6 bg-white shadow-vedic hover:shadow-vedic-hover transition-all duration-300"
        >
            <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center shrink-0 border border-red-500/20">
                    <AlertOctagon className="text-red-600 w-5 h-5" />
                </div>
                <div>
                    <div className="text-[10px] font-bold text-stone-400 uppercase tracking-widest mb-0.5">Karmic Afflictions</div>
                    <h2 className="text-xl font-serif font-bold text-vedic-blue">Advanced Doshas</h2>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {renderDosha("Kala Sarpa Dosha", kalaSarpa, Skull, "purple")}
                {renderDosha("Pitru Dosha", pitru, AlertOctagon, "red")}
            </div>
        </motion.div>
    );
};

export default AdvancedDoshasCard;
