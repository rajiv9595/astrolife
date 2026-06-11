import React from 'react';
import { Sparkles, AlertTriangle } from 'lucide-react';
import { motion } from 'framer-motion';

const PanchangaCard = ({ panchanga }) => {
    if (!panchanga) return null;

    const avakahada = panchanga.avakahada_chakra || {};
    const ghata = panchanga.ghata_chakra || {};

    return (
        <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full border border-stone-200 rounded-2xl p-6 bg-white shadow-vedic hover:shadow-vedic-hover transition-all duration-300"
        >
            <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-vedic-gold/10 flex items-center justify-center shrink-0 border border-vedic-gold/20">
                    <Sparkles className="text-vedic-gold w-5 h-5" />
                </div>
                <div>
                    <div className="text-[10px] font-bold text-stone-400 uppercase tracking-widest mb-0.5">Core Birth Elements</div>
                    <h2 className="text-xl font-serif font-bold text-vedic-blue">Avakahada & Ghata Chakras</h2>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Avakahada Chakra */}
                <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-stone-500 mb-3 flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-vedic-blue"></span>
                        Avakahada Chakra (Nature)
                    </h3>
                    <div className="grid grid-cols-2 gap-2">
                        {Object.entries(avakahada).map(([key, value]) => (
                            <div key={key} className="bg-stone-50 border border-stone-100 p-3 rounded-lg hover:border-vedic-blue/20 transition-colors">
                                <div className="text-[10px] font-bold text-stone-400 uppercase tracking-widest mb-1">{key}</div>
                                <div className="text-sm font-bold text-vedic-blue capitalize">{value}</div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Ghata Chakra */}
                <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-stone-500 mb-3 flex items-center gap-2">
                        <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
                        Ghata Chakra (Inauspicious Elements)
                    </h3>
                    <div className="bg-red-50/30 border border-red-100 rounded-xl p-1 overflow-hidden">
                        <table className="w-full text-sm">
                            <tbody className="divide-y divide-red-100/50">
                                {Object.entries(ghata).map(([key, value]) => (
                                    <tr key={key} className="hover:bg-red-50 transition-colors">
                                        <td className="px-4 py-2.5 font-medium text-stone-600 capitalize">{key}</td>
                                        <td className="px-4 py-2.5 font-bold text-red-700 text-right">{value}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    <p className="text-[10px] text-stone-500 mt-2 ml-1 leading-relaxed">
                        According to classical texts, beginning important ventures during these specific months, lunar days (tithis), weekdays, or nakshatras can bring obstacles.
                    </p>
                </div>
            </div>
        </motion.div>
    );
};

export default PanchangaCard;
