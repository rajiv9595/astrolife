import React, { useState } from 'react';
import { motion } from 'framer-motion';
import classNames from 'classnames';
import { format } from 'date-fns';
import VedicCard from '../ui/VedicCard';

const DashaTimeline = ({ vimshottari }) => {
    if (!vimshottari || !vimshottari.timeline) return null;

    // Find current dasha to expand by default
    const currentDashaIndex = vimshottari.timeline.findIndex(d => d.is_current);
    const [expandedIndex, setExpandedIndex] = useState(currentDashaIndex !== -1 ? currentDashaIndex : 0);

    return (
        <VedicCard className="w-full p-8 bg-white">
            <h3 className="text-xl font-serif font-bold text-vedic-blue mb-6 border-b border-stone-100 pb-2">
                Vimshottari Dasha Timeline
            </h3>

            {/* Scrollable Timeline */}
            <div className="flex gap-4 overflow-x-auto pb-6 custom-scrollbar">
                {vimshottari.timeline.map((dasha, idx) => (
                    <motion.button
                        key={`${dasha.lord}-${idx}`}
                        onClick={() => setExpandedIndex(idx)}
                        className={classNames(
                            "flex-shrink-0 min-w-[140px] p-4 rounded-lg border transition-all text-left relative overflow-hidden",
                            idx === expandedIndex
                                ? "bg-vedic-orange/10 border-vedic-orange shadow-md"
                                : "bg-white border-stone-200 hover:bg-stone-50",
                            dasha.is_current && idx !== expandedIndex && "border-vedic-gold ring-1 ring-vedic-gold ring-offset-2"
                        )}
                        whileHover={{ y: -2 }}
                    >
                        {dasha.is_current && (
                            <div className="absolute top-2 right-2 flex gap-1">
                                <span className="relative flex h-2 w-2">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-vedic-orange opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-vedic-orange"></span>
                                </span>
                            </div>
                        )}
                        <div className={classNames("text-lg font-bold mb-1", idx === expandedIndex ? "text-vedic-orange" : "text-vedic-blue")}>
                            {dasha.lord}
                        </div>
                        <div className="text-xs font-medium text-stone-500">
                            {format(new Date(dasha.start_date), 'yyyy')} - {format(new Date(dasha.end_date), 'yyyy')}
                        </div>
                        <div className="text-[10px] text-vedic-gold font-bold mt-2 uppercase tracking-wide">
                            {dasha.years} Years
                        </div>
                    </motion.button>
                ))}
            </div>

            {/* Expanded Details (Antar Dashas) */}
            <div className="mt-2 p-6 bg-vedic-beige/30 rounded-xl border border-stone-100">
                <h4 className="text-sm font-bold text-vedic-blue mb-4 flex items-center gap-2">
                    <span className="text-vedic-orange text-lg">●</span>
                    Antar Dashas for {vimshottari.timeline[expandedIndex].lord} Mahadasha
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-9 gap-3">
                    {vimshottari.timeline[expandedIndex].antar_dashas?.map((antar, adIdx) => (
                        <div
                            key={adIdx}
                            className={classNames(
                                "p-3 rounded-lg text-center border shadow-sm",
                                antar.is_current ? "bg-white border-vedic-orange text-vedic-orange ring-1 ring-vedic-orange" : "bg-white border-stone-100 text-stone-600"
                            )}
                        >
                            <div className="text-xs font-bold">{antar.lord}</div>
                            <div className="text-[10px] font-medium opacity-80 mt-1">
                                {format(new Date(antar.end_date), 'MMM yy')}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </VedicCard>
    );
};

export default DashaTimeline;
