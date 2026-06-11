import React from 'react';
import { Users, Layout } from 'lucide-react';
import { motion } from 'framer-motion';

const JaiminiCard = ({ jaimini }) => {
    if (!jaimini) return null;

    const karakas = jaimini.chara_karakas || {};
    const arudhas = jaimini.arudha_padas || {};

    return (
        <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full border border-stone-200 rounded-2xl p-6 bg-white shadow-vedic hover:shadow-vedic-hover transition-all duration-300"
        >
            <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-vedic-blue/5 flex items-center justify-center shrink-0 border border-vedic-blue/10">
                    <Users className="text-vedic-blue w-5 h-5" />
                </div>
                <div>
                    <div className="text-[10px] font-bold text-stone-400 uppercase tracking-widest mb-0.5">Advanced System</div>
                    <h2 className="text-xl font-serif font-bold text-vedic-blue">Jaimini Astrology</h2>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Chara Karakas Table */}
                <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-stone-500 mb-3 flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-vedic-orange"></span>
                        Chara Karakas (Significators)
                    </h3>
                    <div className="overflow-hidden border border-stone-100 rounded-xl bg-stone-50/50">
                        <table className="w-full text-sm">
                            <tbody className="divide-y divide-stone-100">
                                {Object.entries(karakas).map(([karaka, planet], idx) => (
                                    <tr key={idx} className="hover:bg-white transition-colors">
                                        <td className="px-4 py-2.5 font-medium text-stone-600">{karaka}</td>
                                        <td className="px-4 py-2.5 font-bold text-vedic-blue text-right">{planet}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Arudha Padas Grid */}
                <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-stone-500 mb-3 flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-vedic-blue"></span>
                        Arudha Padas (Manifestations)
                    </h3>
                    <div className="grid grid-cols-2 gap-2">
                        {Object.entries(arudhas).map(([house, sign], idx) => (
                            <div key={idx} className="flex justify-between items-center bg-white border border-stone-100 px-3 py-2 rounded-lg shadow-2xs hover:border-vedic-blue/20 transition-colors">
                                <span className="text-xs text-stone-500 font-medium">House {house}</span>
                                <span className="text-xs font-bold text-vedic-blue">{sign}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </motion.div>
    );
};

export default JaiminiCard;
