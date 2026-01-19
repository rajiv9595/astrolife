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

const ZODIAC_SYMBOLS = {
    "Aries": "♈", "Taurus": "♉", "Gemini": "♊", "Cancer": "♋",
    "Leo": "♌", "Virgo": "♍", "Libra": "♎", "Scorpio": "♏",
    "Sagittarius": "♐", "Capricorn": "♑", "Aquarius": "♒", "Pisces": "♓"
};

const PLANET_SYMBOLS = {
    "Sun": "☉", "Moon": "☾", "Mars": "♂", "Mercury": "☿",
    "Jupiter": "♃", "Venus": "♀", "Saturn": "♄", "Rahu": "☊", "Ketu": "☋"
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
                    symbol: PLANET_SYMBOLS[planetName] || planetName.substring(0, 2),
                    retrograde: data.retrograde,
                    details: data
                });
            }
        });
    }

    return (
        <div className="w-full aspect-square max-w-lg mx-auto bg-vedic-cream border-2 border-vedic-gold/50 rounded-lg shadow-vedic relative overflow-hidden grid grid-cols-4 grid-rows-4 gap-0">

            {/* Render all 12 signs fixed */}
            {Object.entries(HOUSE_POSITIONS).map(([sign, pos]) => (
                <div
                    key={sign}
                    className="border border-vedic-gold/20 relative p-1 flex flex-wrap content-start gap-1 hover:bg-white/50 transition-colors"
                    style={{ gridRow: pos.row, gridColumn: pos.col }}
                >
                    {/* Sign Label (Subtle, now dark) */}
                    <span className="absolute bottom-0 right-1 text-[10px] text-vedic-muted uppercase tracking-widest pointer-events-none opacity-50">
                        {sign.substring(0, 3)}
                    </span>

                    {/* Planets & Ascendant - Updated colors for light theme */}
                    {signContent[sign].map((item, idx) => {
                        const degreeVal = item.details?.degree || item.details?.norm_deg || item.details?.degree_in_sign || item.details?.degree_in_sign_manual || 0;
                        return (
                            <motion.div
                                key={`${item.name}-${idx}`}
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                className={classNames(
                                    "text-[10px] font-bold px-2 py-0.5 rounded-full cursor-help flex items-center justify-center gap-0.5 shadow-sm border transition-shadow hover:shadow-md",
                                    item.type === 'Asc' ? "bg-vedic-orange text-white border-vedic-orange" : "bg-white text-vedic-blue border-stone-200",
                                    item.retrograde && "text-red-600 border-red-200"
                                )}
                                title={item.type === 'Planet' ? `Degree: ${Number(degreeVal).toFixed(2)}°` : 'Ascendant'}
                            >
                                {item.type === 'Asc' ? 'Lagna' : item.name}
                                {item.retrograde && <span className="text-[8px] opacity-75 ml-0.5">(R)</span>}
                            </motion.div>
                        );
                    })}
                </div>
            ))}

            {/* Center Info Panel - Updated background */}
            <div className="col-start-2 col-span-2 row-start-2 row-span-2 flex flex-col items-center justify-center p-4 text-center border border-vedic-gold/20 bg-white shadow-inner">
                <div className="w-12 h-12 mb-2 opacity-20">
                    <img src="https://cdn-icons-png.flaticon.com/512/2857/2857434.png" alt="Om" />
                    {/* Simple Om icon placeholder or similar */}
                </div>
                <h3 className="text-xl font-serif font-bold text-vedic-orange mb-1">{title}</h3>
                <div className="text-xs text-vedic-muted font-bold">
                    South Indian Style<br />
                    Lahiri Ayanamsha
                </div>
            </div>

        </div>
    );
};

export default SouthIndianChart;
