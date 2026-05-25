import React, { useState } from 'react';
import { Shield, ShieldAlert, ShieldCheck, Flame, Sparkles, Info, BookOpen } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const MangalDoshaCard = ({ mangalDosha }) => {
    const [activeTab, setActiveTab] = useState('Lagna'); // 'Lagna' | 'Moon' | 'Venus'

    if (!mangalDosha) return null;

    const { has_dosha, verdict, details, cancellations_found } = mangalDosha;

    // Decide styles & icons based on the final verdict
    let cardTitle = "Mangal Dosha Analysis";
    let themeClasses = "";
    let statusIcon = null;
    let descriptionText = "";

    if (verdict === "No Dosha") {
        themeClasses = "border-emerald-500/30 bg-emerald-500/5 text-emerald-950";
        statusIcon = <ShieldCheck className="text-emerald-500 w-10 h-10 shrink-0" fill="currentColor" fillOpacity={0.1} />;
        descriptionText = "Excellent! No Mangal Dosha (Kuja Dosha) is present in your charts. Mars is placed in a non-afflicting house.";
    } else if (verdict === "Cancelled") {
        themeClasses = "border-vedic-gold/40 bg-vedic-gold/5 text-stone-900 ring-1 ring-vedic-gold/20";
        statusIcon = <Shield className="text-vedic-gold w-10 h-10 shrink-0 animate-pulse" fill="currentColor" fillOpacity={0.15} />;
        descriptionText = "Mars is situated in a dosha house, but standard Vedic cancellation rules are met. The dosha is completely nullified!";
    } else {
        // Active Dosha: Mild, Medium, High
        themeClasses = "border-red-500/30 bg-red-500/5 text-stone-900 shadow-lg ring-1 ring-red-500/20";
        statusIcon = <Flame className="text-red-500 w-10 h-10 shrink-0 animate-bounce" fill="currentColor" fillOpacity={0.1} />;
        descriptionText = `Attention: A ${verdict} is present. Mars is in an afflicting house from your primary planetary positions.`;
    }

    const currentDetail = details[activeTab] || {};

    return (
        <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            className={`w-full border rounded-2xl p-6 transition-all duration-300 relative overflow-hidden bg-white shadow-vedic hover:shadow-vedic-hover ${themeClasses}`}
        >
            {/* Glowing background highlights */}
            {verdict === "Cancelled" && (
                <div className="absolute top-0 right-0 w-32 h-32 bg-vedic-gold/5 rounded-full blur-3xl -mr-10 -mt-10" />
            )}
            {verdict !== "Cancelled" && verdict !== "No Dosha" && (
                <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/5 rounded-full blur-3xl -mr-10 -mt-10" />
            )}

            {/* Header Area */}
            <div className="flex items-center gap-4 relative z-10">
                {statusIcon}
                <div>
                    <div className="text-[10px] font-bold text-stone-400 uppercase tracking-widest mb-0.5">Vedic Compatibility Factor</div>
                    <div className="flex items-center gap-2">
                        <h2 className="text-2xl font-serif font-bold text-vedic-blue">{cardTitle}</h2>
                        <span className={`px-2.5 py-0.5 text-xs font-bold rounded-full uppercase tracking-wider ${
                            verdict === "No Dosha" ? "bg-emerald-100 text-emerald-700" :
                            verdict === "Cancelled" ? "bg-amber-100 text-amber-800 border border-amber-200/50" :
                            "bg-red-100 text-red-700 animate-pulse"
                        }`}>
                            {verdict}
                        </span>
                    </div>
                </div>
            </div>

            {/* Description Text */}
            <p className="text-sm text-stone-600 mt-4 leading-relaxed relative z-10">
                {descriptionText}
            </p>

            {/* Reference Switch Tabs */}
            <div className="mt-6 flex border-b border-stone-200/80">
                {['Lagna', 'Moon', 'Venus'].map(tab => {
                    const hasD = details[tab]?.is_present;
                    const isC = details[tab]?.is_cancelled;
                    
                    return (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`flex-1 pb-3 text-xs font-bold uppercase tracking-wider transition-all relative ${
                                activeTab === tab 
                                    ? 'text-vedic-blue font-extrabold border-b-2 border-vedic-orange' 
                                    : 'text-stone-400 hover:text-stone-600'
                            }`}
                        >
                            <span>{tab} Chart</span>
                            {hasD && (
                                <span className={`absolute top-0.5 right-2 w-2 h-2 rounded-full ${
                                    isC ? 'bg-vedic-gold' : 'bg-red-500'
                                }`} />
                            )}
                        </button>
                    );
                })}
            </div>

            {/* Tab Details Area */}
            <div className="py-5">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={activeTab}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 10 }}
                        transition={{ duration: 0.15 }}
                        className="space-y-4"
                    >
                        <div className="flex justify-between items-center bg-stone-50/80 border border-stone-100 p-3.5 rounded-xl text-stone-700 text-xs">
                            <div className="flex items-center gap-2">
                                <Info size={14} className="text-stone-400" />
                                <span>Mars position from <strong>{activeTab}</strong>:</span>
                            </div>
                            <span className="font-mono font-bold text-sm bg-white px-2 py-0.5 rounded border border-stone-200/60 shadow-2xs">
                                House {currentDetail.house || 'N/A'}
                            </span>
                        </div>

                        {/* Status Message per chart */}
                        {currentDetail.is_present ? (
                            <div className={`p-4 rounded-xl border flex flex-col gap-2 ${
                                currentDetail.is_cancelled 
                                    ? 'border-vedic-gold/25 bg-vedic-gold/5 text-amber-900' 
                                    : 'border-red-200 bg-red-50/30 text-red-950'
                            }`}>
                                <div className="flex items-center gap-2 font-bold text-xs">
                                    {currentDetail.is_cancelled ? (
                                        <>
                                            <Sparkles size={14} className="text-vedic-gold animate-spin-slow" />
                                            <span>Dosha present in House {currentDetail.house} but Nullified!</span>
                                        </>
                                    ) : (
                                        <>
                                            <Flame size={14} className="text-red-500" />
                                            <span>Active Kuja Dosha in House {currentDetail.house}!</span>
                                        </>
                                    )}
                                </div>
                                {currentDetail.is_cancelled && currentDetail.cancellation_reasons?.length > 0 && (
                                    <div className="mt-2 text-xs border-t border-vedic-gold/20 pt-2 space-y-1.5 text-stone-600">
                                        <div className="font-semibold text-stone-500 uppercase tracking-widest text-[9px] mb-1">Standard Exceptions Satisfied:</div>
                                        {currentDetail.cancellation_reasons.map((reason, idx) => (
                                            <div key={idx} className="flex items-start gap-1.5">
                                                <span className="text-vedic-gold font-bold">✔</span>
                                                <span className="leading-relaxed">{reason}</span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="p-4 rounded-xl border border-emerald-100 bg-emerald-50/20 text-emerald-950 flex items-center gap-2 text-xs font-semibold">
                                <ShieldCheck size={14} className="text-emerald-500" />
                                <span>No dosha observed in this chart reference. Place is auspicious.</span>
                            </div>
                        )}
                    </motion.div>
                </AnimatePresence>
            </div>

            {/* Overall Cancellations Summary (Classical protection banner) */}
            {verdict === "Cancelled" && cancellations_found?.length > 0 && (
                <div className="mt-4 border-t border-stone-200/60 pt-4">
                    <div className="bg-stone-50 p-4 rounded-xl border border-stone-200/50">
                        <h4 className="text-xs font-bold text-vedic-blue flex items-center gap-1.5 mb-2 font-serif">
                            <BookOpen size={14} className="text-vedic-orange" />
                            Classical Astrological Exemption Breakdown
                        </h4>
                        <div className="text-xs text-stone-600 leading-relaxed space-y-2">
                            {cancellations_found.map((c, idx) => (
                                <div key={idx} className="flex items-start gap-2">
                                    <span className="text-vedic-gold text-sm leading-none">✦</span>
                                    <span>{c}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </motion.div>
    );
};

export default MangalDoshaCard;
