import React from 'react';
import { Dumbbell } from 'lucide-react';
import { motion } from 'framer-motion';

const ShadbalaCard = ({ shadbala }) => {
    if (!shadbala) return null;

    // We expect shadbala to be a dict mapping planet name to strength data
    const planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"];

    const getStrengthBadge = (level) => {
        if (level === "High") return <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-emerald-100 text-emerald-700">HIGH</span>;
        if (level === "Medium") return <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-vedic-blue/10 text-vedic-blue">MED</span>;
        return <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-red-100 text-red-700">LOW</span>;
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full border border-stone-200 rounded-2xl p-6 bg-white shadow-vedic hover:shadow-vedic-hover transition-all duration-300"
        >
            <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center shrink-0 border border-purple-500/20">
                    <Dumbbell className="text-purple-600 w-5 h-5" />
                </div>
                <div>
                    <div className="text-[10px] font-bold text-stone-400 uppercase tracking-widest mb-0.5">6-Fold Planetary Strength</div>
                    <h2 className="text-xl font-serif font-bold text-vedic-blue">Shadbala Analysis</h2>
                </div>
            </div>

            <div className="overflow-x-auto border border-stone-100 rounded-xl bg-stone-50/50">
                <table className="w-full text-sm text-left">
                    <thead className="bg-stone-100/50 text-stone-500 text-[10px] uppercase font-bold tracking-wider border-b border-stone-200">
                        <tr>
                            <th className="px-4 py-3">Planet</th>
                            <th className="px-3 py-3 text-center">Positional<br/><span className="font-normal text-stone-400">(Sthana)</span></th>
                            <th className="px-3 py-3 text-center">Directional<br/><span className="font-normal text-stone-400">(Dig)</span></th>
                            <th className="px-3 py-3 text-center">Temporal<br/><span className="font-normal text-stone-400">(Kaala)</span></th>
                            <th className="px-3 py-3 text-center">Motional<br/><span className="font-normal text-stone-400">(Chesta)</span></th>
                            <th className="px-3 py-3 text-center">Natural<br/><span className="font-normal text-stone-400">(Naisargika)</span></th>
                            <th className="px-4 py-3 text-right">Total Rupas</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-100">
                        {planets.map((planet) => {
                            const data = shadbala[planet];
                            if (!data) return null;
                            
                            return (
                                <tr key={planet} className="hover:bg-white transition-colors">
                                    <td className="px-4 py-3 font-bold text-vedic-blue flex items-center gap-2">
                                        {planet} {getStrengthBadge(data.strength_level)}
                                    </td>
                                    <td className="px-3 py-3 text-center text-stone-600">{data.sthana_bala}</td>
                                    <td className="px-3 py-3 text-center text-stone-600">{data.dig_bala}</td>
                                    <td className="px-3 py-3 text-center text-stone-600">{data.kaala_bala}</td>
                                    <td className="px-3 py-3 text-center text-stone-600">{data.chesta_bala}</td>
                                    <td className="px-3 py-3 text-center text-stone-600">{data.naisargika_bala}</td>
                                    <td className="px-4 py-3 text-right font-bold text-vedic-orange text-base">
                                        {data.total_rupas}
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
            
            <div className="mt-4 text-xs text-stone-500 bg-stone-50 p-3 rounded-lg border border-stone-100 flex items-start gap-2">
                <span className="text-vedic-gold font-bold">✦</span>
                <p>
                    <strong>Rupas</strong> represent the combined strength of a planet across six dimensions. 
                    Planets with higher Rupas dominate the chart and their associated Dashas and houses yield more pronounced effects.
                </p>
            </div>
        </motion.div>
    );
};

export default ShadbalaCard;
