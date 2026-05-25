import React from 'react';
import { motion } from 'framer-motion';

const SIGNS_SHORT = {
    "Aries": "Ari", "Taurus": "Tau", "Gemini": "Gem", "Cancer": "Can",
    "Leo": "Leo", "Virgo": "Vir", "Libra": "Lib", "Scorpio": "Sco",
    "Sagittarius": "Sag", "Capricorn": "Cap", "Aquarius": "Aqu", "Pisces": "Pis"
};

const SIGNS_NUM = {
    "Aries": 1, "Taurus": 2, "Gemini": 3, "Cancer": 4, "Leo": 5, "Virgo": 6,
    "Libra": 7, "Scorpio": 8, "Sagittarius": 9, "Capricorn": 10, "Aquarius": 11, "Pisces": 12
};

const PLANET_SHORT = {
    "Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
    "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke"
};

const NorthIndianChart = ({ chartData, title = "Rasi Chart (North Indian)" }) => {
    // 1. Resolve whole sign houses mapping
    const wholeSignHouses = chartData.whole_sign_houses || {};
    
    // Fallback if whole sign houses is empty
    const getHouseSign = (houseNum) => {
        const key = `house_${houseNum}`;
        return wholeSignHouses[key]?.sign || "";
    };

    // 2. Map planets to their respective houses based on signs
    const houseContent = {};
    for (let h = 1; h <= 12; h++) {
        houseContent[h] = [];
    }

    // Add Lagna (Ascendant) to House 1
    houseContent[1].push({ type: 'Asc', label: 'Lagna' });

    // Add planets to their matching sign house
    if (chartData.planets) {
        Object.entries(chartData.planets).forEach(([planetName, data]) => {
            const planetSign = data.sign_manual || data.sign || data.current_sign;
            if (planetSign) {
                // Find which house corresponds to this sign
                for (let h = 1; h <= 12; h++) {
                    if (getHouseSign(h) === planetSign) {
                        houseContent[h].push({
                            type: 'Planet',
                            name: planetName,
                            short: PLANET_SHORT[planetName] || planetName.substring(0, 2),
                            retrograde: data.retrograde,
                            combust: data.combust,
                            degree: data.degree !== undefined ? data.degree : (data.longitude !== undefined ? data.longitude : 0),
                            details: data
                        });
                        break;
                    }
                }
            }
        });
    }

    // 3. Definitions for absolute foreignObject coordinates inside 400x400 SVG box
    // houseConfig defines: { labelX, labelY, contentX, contentY, contentWidth, contentHeight }
    const houseConfig = {
        1: { labelX: 200, labelY: 35, contentX: 120, contentY: 45, width: 160, height: 110 },   // Top Diamond (House 1)
        2: { labelX: 95, labelY: 20, contentX: 20, contentY: 25, width: 130, height: 50 },     // Top-Left (House 2)
        3: { labelX: 20, labelY: 95, contentX: 10, contentY: 45, width: 60, height: 110 },     // Left-Top (House 3)
        4: { labelX: 165, labelY: 200, contentX: 30, contentY: 110, width: 110, height: 180 },  // Left Diamond (House 4)
        5: { labelX: 20, labelY: 305, contentX: 10, contentY: 245, width: 60, height: 110 },    // Left-Bottom (House 5)
        6: { labelX: 95, labelY: 380, contentX: 20, contentY: 325, width: 130, height: 50 },    // Bottom-Left (House 6)
        7: { labelX: 200, labelY: 365, contentX: 120, contentY: 245, width: 160, height: 110 }, // Bottom Diamond (House 7)
        8: { labelX: 305, labelY: 380, contentX: 250, contentY: 325, width: 130, height: 50 },   // Bottom-Right (House 8)
        9: { labelX: 380, labelY: 305, contentX: 330, contentY: 245, width: 60, height: 110 },   // Right-Bottom (House 9)
        10: { labelX: 235, labelY: 200, contentX: 260, contentY: 110, width: 110, height: 180 }, // Right Diamond (House 10)
        11: { labelX: 380, labelY: 95, contentX: 330, contentY: 45, width: 60, height: 110 },   // Right-Top (House 11)
        12: { labelX: 305, labelY: 20, contentX: 250, contentY: 25, width: 130, height: 50 }    // Top-Right (House 12)
    };

    return (
        <div className="w-full max-w-lg mx-auto bg-vedic-cream border-2 border-vedic-gold/50 rounded-lg p-3 shadow-vedic flex flex-col items-center">
            {/* Header Title inside Chart Box */}
            <div className="text-center mb-3">
                <h3 className="text-md font-serif font-bold text-vedic-blue">{title}</h3>
                <p className="text-[10px] text-stone-500 font-bold uppercase tracking-wider">North Indian Style (Lagna Centered)</p>
            </div>

            <div className="w-full aspect-square relative bg-white border border-stone-200 shadow-inner rounded overflow-hidden">
                <svg viewBox="0 0 400 400" className="w-full h-full select-none">
                    {/* Background Grids / Diamonds */}
                    <g stroke="#D17A22" strokeWidth="1.5" strokeOpacity="0.6" fill="none">
                        {/* Outer Square */}
                        <rect x="0" y="0" width="400" height="400" strokeWidth="3" />
                        
                        {/* Diagonals */}
                        <line x1="0" y1="0" x2="400" y2="400" />
                        <line x1="400" y1="0" x2="0" y2="400" />
                        
                        {/* Inner Diamond (Kendra Squares) */}
                        <line x1="200" y1="0" x2="0" y2="200" />
                        <line x1="0" y1="200" x2="200" y2="400" />
                        <line x1="200" y1="400" x2="400" y2="200" />
                        <line x1="400" y1="200" x2="200" y2="0" />
                    </g>

                    {/* Render Content for each House */}
                    {Object.entries(houseConfig).map(([houseNumStr, cfg]) => {
                        const hNum = parseInt(houseNumStr);
                        const signName = getHouseSign(hNum);
                        const signIndex = SIGNS_NUM[signName] || "";
                        const items = houseContent[hNum] || [];

                        // Determine content alignments inside flex boxes based on house shape/position
                        let justifyClass = "justify-center";
                        let itemsClass = "items-center";
                        let flexDir = "flex-row";

                        if (hNum === 4 || hNum === 10) {
                            flexDir = "flex-col";
                        } else if (hNum === 3 || hNum === 5 || hNum === 9 || hNum === 11) {
                            flexDir = "flex-col";
                        }

                        return (
                            <g key={hNum}>
                                {/* Sign Number Label (Standard North Indian format) */}
                                <text
                                    x={cfg.labelX}
                                    y={cfg.labelY}
                                    textAnchor="middle"
                                    dominantBaseline="middle"
                                    className="font-mono text-xs font-bold fill-stone-400"
                                >
                                    {signIndex}
                                </text>

                                {/* Foreign Object for responsive, rich HTML Pills */}
                                <foreignObject
                                    x={cfg.contentX}
                                    y={cfg.contentY}
                                    width={cfg.width}
                                    height={cfg.height}
                                >
                                    <div className={`w-full h-full flex ${flexDir} ${itemsClass} ${justifyClass} flex-wrap gap-1 p-1 overflow-visible`}>
                                        {items.map((item, idx) => {
                                            const degVal = item.degree || 0;
                                            const formattedDeg = `${Math.floor(degVal)}°${Math.floor((degVal % 1) * 60)}'`;

                                            return (
                                                <motion.div
                                                    key={`${item.name || 'Asc'}-${idx}`}
                                                    initial={{ scale: 0 }}
                                                    animate={{ scale: 1 }}
                                                    className={`
                                                        text-[9px] font-extrabold px-1.5 py-0.5 rounded cursor-help flex items-center justify-center gap-0.5 shadow-xs border transition-all hover:shadow-sm
                                                        ${item.type === 'Asc' 
                                                            ? 'bg-vedic-orange text-white border-vedic-orange ring-1 ring-vedic-orange/30' 
                                                            : 'bg-stone-100/70 hover:bg-white text-vedic-blue border-stone-200/60'
                                                        }
                                                        ${item.retrograde ? 'text-red-600 border-red-200 bg-red-50/50' : ''}
                                                    `}
                                                    title={item.type === 'Planet' ? `${item.name} in ${signName}: ${formattedDeg}` : 'Ascendant (Lagna)'}
                                                >
                                                    <span>{item.type === 'Asc' ? 'Lagn' : item.short}</span>
                                                    {item.retrograde && <span className="text-[7px] text-red-500 font-bold">(R)</span>}
                                                    {item.type === 'Planet' && (
                                                        <span className="text-[7px] text-stone-400 font-mono font-normal">
                                                            {Math.floor(degVal)}°
                                                        </span>
                                                    )}
                                                </motion.div>
                                            );
                                        })}
                                    </div>
                                </foreignObject>
                            </g>
                        );
                    })}
                </svg>
            </div>
            
            {/* Footer Sign Indicator legend */}
            <div className="w-full mt-2 bg-stone-50/50 rounded p-2 border border-stone-100 flex items-center justify-center flex-wrap gap-x-3 gap-y-1 text-[10px] text-stone-500">
                <span className="font-bold">Signs Code:</span>
                {Object.entries(SIGNS_SHORT).map(([signName, shortName]) => (
                    <div key={signName} className="flex items-center gap-0.5">
                        <strong className="text-stone-700 font-mono font-bold">{SIGNS_NUM[signName]}</strong>
                        <span>=</span>
                        <span className="text-vedic-muted">{shortName}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default NorthIndianChart;
