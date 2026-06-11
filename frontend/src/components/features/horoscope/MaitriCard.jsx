import React, { useState } from 'react';
import { Network } from 'lucide-react';
import { motion } from 'framer-motion';

const PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"];

const MaitriCard = ({ maitri }) => {
    const [view, setView] = useState('compound'); // 'natural' | 'temporal' | 'compound'

    if (!maitri) return null;

    const getColorClass = (rel) => {
        switch(rel) {
            case "Best Friend": return "text-emerald-600 bg-emerald-50";
            case "Friend": return "text-emerald-500 bg-emerald-50/50";
            case "Neutral": return "text-stone-500 bg-stone-50";
            case "Enemy": return "text-red-500 bg-red-50/50";
            case "Bitter Enemy": return "text-red-600 bg-red-50 font-bold";
            default: return "text-stone-300";
        }
    };

    const getShortLabel = (rel) => {
        if (rel === "Best Friend") return "Best Frnd";
        if (rel === "Bitter Enemy") return "B. Enemy";
        return rel;
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full border border-stone-200 rounded-2xl p-6 bg-white shadow-vedic hover:shadow-vedic-hover transition-all duration-300"
        >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center shrink-0 border border-indigo-500/20">
                        <Network className="text-indigo-600 w-5 h-5" />
                    </div>
                    <div>
                        <div className="text-[10px] font-bold text-stone-400 uppercase tracking-widest mb-0.5">Planetary Relationships</div>
                        <h2 className="text-xl font-serif font-bold text-vedic-blue">Maitri Chakra</h2>
                    </div>
                </div>

                <div className="flex gap-1 bg-stone-100 p-1 rounded-lg">
                    {['natural', 'temporal', 'compound'].map(t => (
                        <button
                            key={t}
                            onClick={() => setView(t)}
                            className={`px-3 py-1.5 rounded-md text-[10px] uppercase tracking-widest font-bold transition-colors ${
                                view === t ? 'bg-white text-vedic-blue shadow-sm' : 'text-stone-500 hover:text-stone-700'
                            }`}
                        >
                            {t}
                        </button>
                    ))}
                </div>
            </div>

            <div className="overflow-x-auto border border-stone-100 rounded-xl">
                <table className="w-full text-xs text-center">
                    <thead className="bg-stone-50 border-b border-stone-100">
                        <tr>
                            <th className="px-2 py-3 text-left font-bold text-stone-400 uppercase tracking-wider pl-4">Planet</th>
                            {PLANETS.map(p => (
                                <th key={p} className="px-2 py-3 font-bold text-vedic-blue">{p}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-100">
                        {PLANETS.map(p1 => (
                            <tr key={p1} className="hover:bg-stone-50/50">
                                <td className="px-4 py-3 font-bold text-vedic-blue text-left border-r border-stone-100 bg-stone-50/30">
                                    {p1}
                                </td>
                                {PLANETS.map(p2 => {
                                    if (p1 === p2) return <td key={p2} className="px-2 py-3 text-stone-300 bg-stone-50/30">-</td>;
                                    const rel = maitri[p1]?.[p2]?.[view];
                                    return (
                                        <td key={p2} className={`px-2 py-3 font-medium transition-colors ${getColorClass(rel)}`}>
                                            {getShortLabel(rel)}
                                        </td>
                                    );
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            
            <p className="text-[10px] text-stone-500 mt-4 text-center">
                Read horizontally: The relationship of the row planet <strong>towards</strong> the column planet.
            </p>
        </motion.div>
    );
};

export default MaitriCard;
