import React from 'react';
import { Activity } from 'lucide-react';
import { motion } from 'framer-motion';

const SIGNS_LIST = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
];

const AshtakavargaCard = ({ ashtakavarga }) => {
    if (!ashtakavarga || !ashtakavarga.sav) return null;

    const savPoints = ashtakavarga.sav;

    // Helper to determine color based on strength
    const getStrengthColor = (points) => {
        if (points >= 30) return "bg-emerald-500 text-white border-emerald-600";
        if (points >= 25) return "bg-vedic-blue text-white border-vedic-blue";
        if (points >= 20) return "bg-amber-400 text-amber-950 border-amber-500";
        return "bg-red-400 text-white border-red-500";
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full border border-stone-200 rounded-2xl p-6 bg-white shadow-vedic hover:shadow-vedic-hover transition-all duration-300"
        >
            <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center shrink-0 border border-emerald-500/20">
                    <Activity className="text-emerald-600 w-5 h-5" />
                </div>
                <div>
                    <div className="text-[10px] font-bold text-stone-400 uppercase tracking-widest mb-0.5">Strength Matrix</div>
                    <h2 className="text-xl font-serif font-bold text-vedic-blue">Samudaya Ashtakavarga (SAV)</h2>
                </div>
            </div>

            <p className="text-xs text-stone-500 mb-6 leading-relaxed max-w-2xl">
                The total benefic points for each zodiac sign. Signs with <strong>30+ points</strong> yield excellent results during transits, 25-29 are average, and below 25 yield challenging results.
            </p>

            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                {savPoints.map((points, idx) => (
                    <div key={idx} className="flex flex-col border border-stone-100 rounded-xl overflow-hidden bg-stone-50 hover:border-stone-300 transition-colors">
                        <div className="bg-white py-2 text-center border-b border-stone-100">
                            <span className="text-xs font-bold text-stone-600 uppercase tracking-wider">{SIGNS_LIST[idx]}</span>
                        </div>
                        <div className={`py-3 text-center flex-1 flex items-center justify-center ${getStrengthColor(points)}`}>
                            <span className="text-xl font-serif font-black">{points}</span>
                        </div>
                    </div>
                ))}
            </div>
        </motion.div>
    );
};

export default AshtakavargaCard;
