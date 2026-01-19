import React, { useEffect, useState } from 'react';
import { authService } from '../services/authService';
import { astroService } from '../services/astroService';
import VedicCard from '../components/ui/VedicCard';
import { RefreshCw, Download, ChevronRight, Calendar } from 'lucide-react';
import { toast } from 'react-toastify';
import { motion } from 'framer-motion';

const DashaPage = () => {
    const [chartData, setChartData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [selectedMahadashaIdx, setSelectedMahadashaIdx] = useState(null);
    const [user, setUser] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const currentUser = await authService.getCurrentUser();
                setUser(currentUser);

                // Try to get data from local storage or context if possible, 
                // but for now we fetch fresh to ensure accuracy
                const params = await authService.getChartDataParams();
                const data = await astroService.computeChart(params);
                setChartData(data);

                // Find current mahadasha to select by default
                if (data?.vimshottari?.timeline) {
                    const currentIdx = data.vimshottari.timeline.findIndex(d => d.is_current);
                    if (currentIdx !== -1) setSelectedMahadashaIdx(currentIdx);
                    else setSelectedMahadashaIdx(0);
                }
            } catch (err) {
                console.error(err);
                toast.error("Could not load Dasha data.");
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-96 gap-4">
                <div className="w-12 h-12 border-4 border-vedic-orange border-t-transparent rounded-full animate-spin" />
                <p className="text-vedic-blue font-bold animate-pulse">Calculating Planetary Periods...</p>
            </div>
        );
    }

    if (!chartData?.vimshottari?.timeline) {
        return <div className="p-8 text-center text-red-500">No Dasha data available.</div>;
    }

    const { timeline } = chartData.vimshottari;
    const activeMahadasha = selectedMahadashaIdx !== null ? timeline[selectedMahadashaIdx] : null;

    return (
        <div className="space-y-6">
            {/* Header / Title Section */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-stone-200 pb-4">
                <div>
                    <h1 className="text-3xl font-serif font-bold text-vedic-blue">Vimshottari Dasha Timeline</h1>
                    <p className="text-sm text-stone-500 mt-1">
                        Track your current and future life periods based on the Moon's position.
                    </p>
                </div>
                {user && (
                    <div className="text-right hidden md:block">
                        <div className="text-sm font-bold text-vedic-blue">{user.name}</div>
                        <div className="text-xs text-stone-500">Lahiri Ayanamsha</div>
                    </div>
                )}
            </div>

            {/* Mahadasha Selection / Timeline Strip */}
            <div className="bg-white rounded-lg shadow-sm border border-stone-100 p-2 overflow-x-auto">
                <div className="flex gap-2 min-w-max">
                    {timeline.map((dasha, idx) => (
                        <button
                            key={`${dasha.lord}-${idx}`}
                            onClick={() => setSelectedMahadashaIdx(idx)}
                            className={`
                                flex flex-col items-center p-3 rounded-md min-w-[100px] transition-all relative
                                ${selectedMahadashaIdx === idx
                                    ? 'bg-vedic-blue text-white shadow-md transform scale-105 z-10'
                                    : 'hover:bg-vedic-orange/10 text-stone-600'
                                }
                                ${dasha.is_current && selectedMahadashaIdx !== idx ? 'ring-2 ring-vedic-orange ring-offset-1' : ''}
                            `}
                        >
                            <span className="text-xs font-bold uppercase tracking-wider mb-1">{dasha.lord}</span>
                            <span className="text-[10px] opacity-80">{dasha.start_date.split('T')[0].split('-')[0]}</span>
                            {dasha.is_current && (
                                <span className="absolute -top-1 -right-1 w-3 h-3 bg-vedic-orange rounded-full border-2 border-white" />
                            )}
                        </button>
                    ))}
                </div>
            </div>

            {/* Active Mahadasha Content */}
            {activeMahadasha && (
                <div className="space-y-6">
                    {/* Mahadasha Header Card */}
                    <div className="bg-vedic-blue rounded-lg p-6 text-white shadow-lg relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full blur-3xl -mr-10 -mt-10" />

                        <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 relative z-10">
                            <div>
                                <div className="flex items-center gap-3 mb-2">
                                    <h2 className="text-4xl font-serif font-bold text-vedic-orange">{activeMahadasha.lord}</h2>
                                    <span className="px-2 py-1 bg-white/10 rounded text-xs uppercase tracking-wider">Mahadasha</span>
                                    {activeMahadasha.is_partial && <span className="text-xs text-stone-400">(Partial)</span>}
                                </div>
                                <div className="flex items-center gap-2 text-stone-300 text-sm">
                                    <Calendar size={14} />
                                    <span>{formatDate(activeMahadasha.start_date)}</span>
                                    <span className="text-stone-500 mx-1">➜</span>
                                    <span>{formatDate(activeMahadasha.end_date)}</span>
                                </div>
                            </div>

                            <div className="text-right">
                                <span className="text-2xl font-bold">{activeMahadasha.years}</span>
                                <span className="text-sm ml-1 text-stone-400">Years Duration</span>
                            </div>
                        </div>
                    </div>

                    {/* Antardasha Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                        {activeMahadasha.antar_dashas.map((antar, aIdx) => (
                            <motion.div
                                key={antar.lord + aIdx}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: aIdx * 0.05 }}
                                className={`
                                    flex flex-col bg-white rounded-xl shadow-sm border
                                    ${antar.is_current ? 'border-vedic-orange shadow-md ring-1 ring-vedic-orange/20' : 'border-stone-100'}
                                `}
                            >
                                {/* Antardasha Header */}
                                <div className={`p-4 border-b ${antar.is_current ? 'bg-vedic-orange/5 border-vedic-orange/20' : 'border-stone-50'}`}>
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <h3 className="text-xl font-bold text-vedic-blue">{antar.lord}</h3>
                                            <p className="text-xs text-stone-500 font-medium mt-1">
                                                {formatDate(antar.start_date)} <span className="mx-1">→</span> {formatDate(antar.end_date)}
                                            </p>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-xs font-mono font-bold text-vedic-orange">
                                                {antar.years < 1
                                                    ? `${Math.round(antar.years * 12)} months`
                                                    : `${Number(antar.years).toFixed(2)} Years`
                                                }
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Pratyantardasha List */}
                                <div className="flex-1 p-4 bg-stone-50/30">
                                    <div className="space-y-2">
                                        {antar.pratyantar_dashas.map((prat, pIdx) => (
                                            <div
                                                key={prat.lord + pIdx}
                                                className={`
                                                    flex justify-between items-center text-xs p-2 rounded
                                                    ${prat.is_current ? 'bg-vedic-orange/10 text-vedic-blue font-bold border border-vedic-orange/20' : 'text-stone-600 hover:bg-stone-50'}
                                                `}
                                            >
                                                <div className="w-16 font-medium">{prat.lord}</div>
                                                <div className="flex-1 text-right text-[10px] text-stone-500 font-mono">
                                                    {formatDateShort(prat.start_date)} - {formatDateShort(prat.end_date)}
                                                </div>
                                                <div className="w-16 text-right font-mono text-stone-400">
                                                    {Math.round(prat.years * 365) < 30
                                                        ? `${Math.round(prat.years * 365)}d`
                                                        : `${Math.round(prat.years * 12)}m`
                                                    }
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

// Utilities
const formatDate = (isoString) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' });
};

const formatDateShort = (isoString) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: '2-digit' });
};

export default DashaPage;
