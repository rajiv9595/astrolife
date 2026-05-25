import React from 'react';
import { motion } from 'framer-motion';
import classNames from 'classnames';

// Fixed South Indian Layout Mapping
// 0: Pisces, 1: Aries, 2: Taurus, etc.
// Grid coordinates (row, col) 1-based
const HOUSE_POSITIONS = {
    "Pisces": { row: 1, col: 1 },
    "Aries": { row: 1, col: 2 },
    "Taurus": { row: 1, col: 3 },
    "Gemini": { row: 1, col: 4 },
    "Cancer": { row: 2, col: 4 },
    "Leo": { row: 3, col: 4 },
    "Virgo": { row: 4, col: 4 },
    "Libra": { row: 4, col: 3 },
    "Scorpio": { row: 4, col: 2 },
    "Sagittarius": { row: 4, col: 1 },
    "Capricorn": { row: 3, col: 1 },
    "Aquarius": { row: 2, col: 1 },
};

const PLANET_SHORT = {
    "Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
    "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke"
};

const SouthIndianChart = ({ chartData, title = "Rasi Chart" }) => {
    const signContent = {};
    Object.keys(HOUSE_POSITIONS).forEach(sign => signContent[sign] = []);

    if (chartData.ascendant) {
        const ascSign = chartData.ascendant.sign;
        if (signContent[ascSign]) {
            signContent[ascSign].push({ type: 'Asc', label: 'L' });
        }
    }

    if (chartData.planets) {
        Object.entries(chartData.planets).forEach(([planetName, data]) => {
            const sign = data.sign_manual || data.sign || data.current_sign;
            if (sign && signContent[sign]) {
                signContent[sign].push({
                    type: 'Planet',
                    name: planetName,
                    short: PLANET_SHORT[planetName] || planetName.substring(0, 2),
                    retrograde: data.retrograde,
                    combust: data.combust,
                    degree: data.degree !== undefined ? data.degree : (data.longitude !== undefined ? data.longitude : 0),
                    details: data
                });
            }
        });
    }

    return (
        <div className="w-full aspect-square max-w-lg mx-auto bg-vedic-cream border-2 border-vedic-gold/50 rounded-lg shadow-vedic relative overflow-hidden grid grid-cols-4 grid-rows-4 gap-0 p-1">

            {/* Render all 12 signs fixed */}
            {Object.entries(HOUSE_POSITIONS).map(([sign, pos]) => (
                <div
                    key={sign}
                    className="border border-vedic-gold/20 relative p-1.5 flex flex-wrap content-start gap-1 hover:bg-white/50 transition-colors"
                    style={{ gridRow: pos.row, gridColumn: pos.col }}
                >
                    {/* Sign Label (Subtle, bottom right) */}
                    <span className="absolute bottom-0.5 right-1 text-[9px] text-stone-400 font-bold uppercase tracking-wider pointer-events-none opacity-60">
                        {sign.substring(0, 3)}
                    </span>

                    {/* Planets & Ascendant - Compact Degree Layout */}
                    {signContent[sign].map((item, idx) => {
                        const degreeVal = item.degree || 0;
                        const formattedDeg = `${Math.floor(degreeVal)}°${Math.floor((degreeVal % 1) * 60)}'`;
                        
                        return (
                            <motion.div
                                key={`${item.name || 'Asc'}-${idx}`}
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                className={classNames(
                                    "text-[9px] font-extrabold px-1.5 py-0.5 rounded cursor-help flex items-center justify-center gap-0.5 shadow-xs border transition-all hover:shadow-sm",
                                    item.type === 'Asc' 
                                        ? "bg-vedic-orange text-white border-vedic-orange ring-1 ring-vedic-orange/20" 
                                        : "bg-white text-vedic-blue border-stone-200",
                                    item.retrograde && "text-red-600 border-red-200 bg-red-50/50"
                                )}
                                title={item.type === 'Planet' ? `${item.name} in ${sign}: ${formattedDeg}` : 'Ascendant (Lagna)'}
                            >
                                <span>{item.type === 'Asc' ? 'Lagn' : item.short}</span>
                                {item.retrograde && <span className="text-[7px] text-red-500 font-bold">(R)</span>}
                                {item.type === 'Planet' && (
                                    <span className="text-[7px] text-stone-400 font-mono font-normal">
                                        {Math.floor(degreeVal)}°
                                    </span>
                                )}
                            </motion.div>
                        );
                    })}
                </div>
            ))}

            {/* Center Info Panel */}
            <div className="col-start-2 col-span-2 row-start-2 row-span-2 flex flex-col items-center justify-center p-4 text-center border border-vedic-gold/20 bg-white shadow-inner">
                <div className="w-10 h-10 mb-2 text-vedic-orange opacity-80 flex items-center justify-center">
                    <svg viewBox="0 0 24 24" className="w-full h-full stroke-current fill-none stroke-[1.5]" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="12" cy="12" r="4" />
                        <circle cx="12" cy="12" r="8" strokeDasharray="3 3" />
                        <path d="M12 2v3M12 19v3M2 12h3M19 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1" />
                    </svg>
                </div>
                <h3 className="text-lg font-serif font-bold text-vedic-orange leading-tight mb-0.5">{title}</h3>
                <div className="text-[10px] text-stone-400 font-bold uppercase tracking-wider">
                    South Indian Style<br />
                    Lahiri Ayanamsha
                </div>
            </div>

        </div>
    );
};

export default SouthIndianChart;
