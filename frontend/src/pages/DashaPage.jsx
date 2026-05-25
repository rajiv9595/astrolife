import React, { useEffect, useState } from 'react';
import { authService } from '../services/authService';
import { astroService } from '../services/astroService';
import VedicCard from '../components/ui/VedicCard';
import { RefreshCw, Download, ChevronRight, ChevronDown, Calendar, Clock, Sparkles } from 'lucide-react';
import { toast } from 'react-toastify';
import { motion, AnimatePresence } from 'framer-motion';

const DashaPage = () => {
    const [chartData, setChartData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [selectedMahadashaIdx, setSelectedMahadashaIdx] = useState(null);
    const [expandedPratKey, setExpandedPratKey] = useState(null); // Format: "antarLord-pratLord"
    const [user, setUser] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const currentUser = await authService.getCurrentUser();
                setUser(currentUser);

                // Fetch fresh to ensure accuracy and compute Sookshma/Prana levels
                const params = await authService.getChartDataParams();
                const data = await astroService.computeChart(params);
                setChartData(data);

                // Find current mahadasha to select by default
                if (data?.vimshottari?.timeline) {
                    const currentIdx = data.vimshottari.timeline.findIndex(d => d.is_current);
                    if (currentIdx !== -1) {
                        setSelectedMahadashaIdx(currentIdx);
                        // Also auto-expand current active Antar/Pratyantar dasha
                        const currentMahadasha = data.vimshottari.timeline[currentIdx];
                        const currentAntar = currentMahadasha.antar_dashas?.find(ad => ad.is_current);
                        const currentPrat = currentAntar?.pratyantar_dashas?.find(pd => pd.is_current);
                        if (currentAntar && currentPrat) {
                            setExpandedPratKey(`${currentAntar.lord}-${currentPrat.lord}`);
                        }
                    } else {
                        setSelectedMahadashaIdx(0);
                    }
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
                <p className="text-vedic-blue font-bold animate-pulse">Calculating High-Precision Planetary Periods...</p>
            </div>
        );
    }

    if (!chartData?.vimshottari?.timeline) {
        return <div className="p-8 text-center text-red-500">No Dasha data available.</div>;
    }

    const { timeline } = chartData.vimshottari;
    const activeMahadasha = selectedMahadashaIdx !== null ? timeline[selectedMahadashaIdx] : null;

    // Extract current active dasha path down to Pranadasha
    const getActiveDashaPath = () => {
        const mahadasha = timeline.find(d => d.is_current);
        if (!mahadasha) return null;

        const antar = mahadasha.antar_dashas?.find(d => d.is_current);
        if (!antar) return { mahadasha };

        const pratyantar = antar.pratyantar_dashas?.find(d => d.is_current);
        if (!pratyantar) return { mahadasha, antar };

        const sookshma = pratyantar.sookshma_dashas?.find(d => d.is_current);
        if (!sookshma) return { mahadasha, antar, pratyantar };

        const prana = sookshma.prana_dashas?.find(d => d.is_current);
        return { mahadasha, antar, pratyantar, sookshma, prana };
    };

    const activePath = getActiveDashaPath();

    const toggleExpandPrat = (antarLord, pratLord) => {
        const key = `${antarLord}-${pratLord}`;
        setExpandedPratKey(expandedPratKey === key ? null : key);
    };

    return (
        <div className="space-y-6 max-w-7xl mx-auto px-4 md:px-0">
            {/* Header / Title Section */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-stone-200 pb-4">
                <div>
                    <h1 className="text-3xl font-serif font-bold text-vedic-blue">Vimshottari Dasha Timeline</h1>
                    <p className="text-sm text-stone-500 mt-1">
                        Track your current and future life periods from Mahadasha down to Pranadasha.
                    </p>
                </div>
                {user && (
                    <div className="text-right hidden md:block">
                        <div className="text-sm font-bold text-vedic-blue">{user.name}</div>
                        <div className="text-xs text-stone-500">Lahiri Ayanamsha (Sidereal)</div>
                    </div>
                )}
            </div>

            {/* Glowing Premium Live Dasha Path Banner */}
            {activePath && (
                <div className="bg-gradient-to-r from-stone-900 via-stone-800 to-stone-900 border border-stone-700/60 rounded-xl p-5 text-white shadow-xl relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-48 h-48 bg-vedic-orange/5 rounded-full blur-3xl -mr-16 -mt-16" />
                    
                    <div className="flex items-center gap-2 mb-3">
                        <Sparkles className="text-vedic-orange animate-pulse" size={16} />
                        <span className="text-xs uppercase tracking-widest text-vedic-orange font-bold font-mono">Current Astrological Period</span>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 md:gap-3 text-stone-100">
                        {/* Mahadasha */}
                        <div className="flex items-center gap-2 bg-stone-800/80 px-3 py-2 rounded-lg border border-stone-700/50">
                            <div className="text-left">
                                <p className="text-[9px] uppercase tracking-wider text-stone-400">Mahadasha</p>
                                <p className="text-sm font-bold text-vedic-orange">{activePath.mahadasha.lord}</p>
                            </div>
                        </div>

                        <ChevronRight className="text-stone-600 hidden sm:block" size={16} />

                        {/* Antardasha */}
                        {activePath.antar && (
                            <div className="flex items-center gap-2 bg-stone-800/80 px-3 py-2 rounded-lg border border-stone-700/50">
                                <div className="text-left">
                                    <p className="text-[9px] uppercase tracking-wider text-stone-400">Antardasha</p>
                                    <p className="text-sm font-bold text-stone-100">{activePath.antar.lord}</p>
                                </div>
                            </div>
                        )}

                        {activePath.antar && <ChevronRight className="text-stone-600 hidden sm:block" size={16} />}

                        {/* Pratyantardasha */}
                        {activePath.pratyantar && (
                            <div className="flex items-center gap-2 bg-stone-800/80 px-3 py-2 rounded-lg border border-stone-700/50">
                                <div className="text-left">
                                    <p className="text-[9px] uppercase tracking-wider text-stone-400">Pratyantar</p>
                                    <p className="text-sm font-bold text-stone-100">{activePath.pratyantar.lord}</p>
                                </div>
                            </div>
                        )}

                        {activePath.pratyantar && <ChevronRight className="text-stone-600 hidden sm:block" size={16} />}

                        {/* Sookshmadasha */}
                        {activePath.sookshma && (
                            <div className="flex items-center gap-2 bg-stone-800/80 px-3 py-2 rounded-lg border border-stone-700/50 ring-1 ring-vedic-orange/30">
                                <div className="text-left">
                                    <p className="text-[9px] uppercase tracking-wider text-vedic-orange font-bold">Sookshma</p>
                                    <p className="text-sm font-bold text-vedic-orange">{activePath.sookshma.lord}</p>
                                </div>
                            </div>
                        )}

                        {activePath.sookshma && <ChevronRight className="text-stone-600 hidden sm:block" size={16} />}

                        {/* Pranadasha */}
                        {activePath.prana && (
                            <div className="flex items-center gap-2 bg-stone-800/80 px-3 py-2 rounded-lg border border-stone-700/50 ring-1 ring-white/30">
                                <div className="text-left">
                                    <p className="text-[9px] uppercase tracking-wider text-stone-300 font-bold font-mono">Prana (Hour)</p>
                                    <p className="text-sm font-bold text-stone-100 animate-pulse">{activePath.prana.lord}</p>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Active Period Duration Indicator */}
                    <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-stone-400 border-t border-stone-800/80 pt-3">
                        <div className="flex items-center gap-1">
                            <Clock size={12} className="text-vedic-orange" />
                            <span>Active Sookshma:</span>
                            <strong className="text-white font-mono">{formatDateWithTime(activePath.sookshma?.start_date)}</strong>
                            <span>to</span>
                            <strong className="text-white font-mono">{formatDateWithTime(activePath.sookshma?.end_date)}</strong>
                        </div>
                    </div>
                </div>
            )}

            {/* Mahadasha Selection / Timeline Strip */}
            <div className="bg-white rounded-lg shadow-sm border border-stone-100 p-2 overflow-x-auto">
                <div className="flex gap-2 min-w-max">
                    {timeline.map((dasha, idx) => (
                        <button
                            key={`${dasha.lord}-${idx}`}
                            onClick={() => {
                                setSelectedMahadashaIdx(idx);
                                setExpandedPratKey(null); // reset expand on switch
                            }}
                            className={`
                                flex flex-col items-center p-3 rounded-md min-w-[110px] transition-all relative
                                ${selectedMahadashaIdx === idx
                                    ? 'bg-vedic-blue text-white shadow-md transform scale-105 z-10 font-bold'
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
                                    {activeMahadasha.is_partial && <span className="text-xs text-stone-400">(Partial at birth)</span>}
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
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {activeMahadasha.antar_dashas.map((antar, aIdx) => (
                            <motion.div
                                key={antar.lord + aIdx}
                                initial={{ opacity: 0, y: 15 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: aIdx * 0.05 }}
                                className={`
                                    flex flex-col bg-white rounded-xl shadow-sm border transition-all duration-300
                                    ${antar.is_current ? 'border-vedic-orange shadow-md ring-1 ring-vedic-orange/20' : 'border-stone-100 hover:border-stone-200'}
                                `}
                            >
                                {/* Antardasha Header */}
                                <div className={`p-4 border-b ${antar.is_current ? 'bg-vedic-orange/5 border-vedic-orange/20' : 'border-stone-50'}`}>
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <h3 className="text-xl font-bold text-vedic-blue flex items-center gap-2">
                                                {antar.lord}
                                                {antar.is_current && (
                                                    <span className="px-1.5 py-0.5 bg-vedic-orange/15 text-vedic-orange text-[9px] uppercase tracking-wider rounded font-bold">Active</span>
                                                )}
                                            </h3>
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
                                <div className="flex-1 p-4 bg-stone-50/20">
                                    <p className="text-[10px] text-stone-400 uppercase tracking-widest font-bold mb-2">Pratyantar Dashas (Click to expand Sookshma)</p>
                                    <div className="space-y-2">
                                        {antar.pratyantar_dashas.map((prat, pIdx) => {
                                            const pratKey = `${antar.lord}-${prat.lord}`;
                                            const isExpanded = expandedPratKey === pratKey;

                                            return (
                                                <div key={prat.lord + pIdx} className="border border-stone-100 rounded-lg overflow-hidden bg-white">
                                                    {/* Pratyantar Row Toggle */}
                                                    <button
                                                        onClick={() => toggleExpandPrat(antar.lord, prat.lord)}
                                                        className={`
                                                            w-full flex justify-between items-center text-xs p-3 transition-colors
                                                            ${prat.is_current ? 'bg-vedic-orange/5 text-vedic-blue font-bold' : 'text-stone-700 hover:bg-stone-50/50'}
                                                        `}
                                                    >
                                                        <div className="flex items-center gap-2">
                                                            {isExpanded ? <ChevronDown size={14} className="text-stone-400" /> : <ChevronRight size={14} className="text-stone-400" />}
                                                            <span className="font-semibold text-stone-800">{prat.lord}</span>
                                                            {prat.is_current && (
                                                                <span className="w-1.5 h-1.5 bg-vedic-orange rounded-full" />
                                                            )}
                                                        </div>
                                                        <div className="flex-1 text-right text-[10px] text-stone-500 font-mono pr-3">
                                                            {formatDateShort(prat.start_date)} - {formatDateShort(prat.end_date)}
                                                        </div>
                                                        <div className="w-16 text-right font-mono text-stone-400">
                                                            {Math.round(prat.years * 365) < 30
                                                                ? `${Math.round(prat.years * 365)}d`
                                                                : `${Math.round(prat.years * 12)}m`
                                                            }
                                                        </div>
                                                    </button>

                                                    {/* Nested Sookshmadashas (AnimatePresence slide down) */}
                                                    <AnimatePresence>
                                                        {isExpanded && prat.sookshma_dashas && (
                                                            <motion.div
                                                                initial={{ height: 0, opacity: 0 }}
                                                                animate={{ height: "auto", opacity: 1 }}
                                                                exit={{ height: 0, opacity: 0 }}
                                                                transition={{ duration: 0.25 }}
                                                                className="border-t border-stone-50 bg-stone-50/40 p-2.5 space-y-1.5"
                                                            >
                                                                <p className="text-[9px] uppercase tracking-wider text-vedic-orange font-bold pl-1 mb-1">Sookshma Dashas (Sub-sub-periods)</p>
                                                                {prat.sookshma_dashas.map((sook, sIdx) => (
                                                                    <div key={sook.lord + sIdx} className="space-y-1.5">
                                                                        <div
                                                                            className={`
                                                                                flex justify-between items-center text-[11px] p-2 rounded border
                                                                                ${sook.is_current 
                                                                                    ? 'bg-vedic-orange/10 border-vedic-orange/30 text-vedic-blue font-bold shadow-xs' 
                                                                                    : 'bg-white border-stone-100 text-stone-600 hover:bg-stone-50/60'
                                                                                }
                                                                            `}
                                                                        >
                                                                            <div className="font-medium flex items-center gap-1.5">
                                                                                <span className="w-1 h-1 bg-stone-400 rounded-full" />
                                                                                {sook.lord}
                                                                            </div>
                                                                            <div className="text-[10px] text-stone-500 font-mono">
                                                                                {formatDateWithTimeShort(sook.start_date)} - {formatDateWithTimeShort(sook.end_date)}
                                                                            </div>
                                                                            <div className="font-mono text-[10px] text-stone-400">
                                                                                {Math.round(sook.years * 365) < 1 
                                                                                    ? `${Math.round(sook.years * 365 * 24)}h`
                                                                                    : `${Math.round(sook.years * 365)}d`
                                                                                }
                                                                            </div>
                                                                        </div>

                                                                        {/* Nested Pranadashas for current Sookshmadasha */}
                                                                        {sook.is_current && sook.prana_dashas && (
                                                                            <div className="pl-4 pr-1 py-1 space-y-1 bg-stone-100/50 rounded border border-stone-200/50">
                                                                                <p className="text-[8px] uppercase tracking-widest text-stone-500 font-bold mb-1">Prana Dashas (Current Hour Level)</p>
                                                                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-1">
                                                                                    {sook.prana_dashas.map((pran, prIdx) => (
                                                                                        <div
                                                                                            key={pran.lord + prIdx}
                                                                                            className={`
                                                                                                flex justify-between items-center text-[9px] px-2 py-1 rounded
                                                                                                ${pran.is_current 
                                                                                                    ? 'bg-white text-vedic-orange font-bold ring-1 ring-vedic-orange/30 shadow-xs' 
                                                                                                    : 'text-stone-500 bg-stone-50/60'
                                                                                                }
                                                                                            `}
                                                                                        >
                                                                                            <span className="font-semibold uppercase tracking-wider">{pran.lord}</span>
                                                                                            <span className="font-mono text-[8px] opacity-85">
                                                                                                {formatTimeOnly(pran.start_date)} - {formatTimeOnly(pran.end_date)}
                                                                                            </span>
                                                                                        </div>
                                                                                    ))}
                                                                                </div>
                                                                            </div>
                                                                        )}
                                                                    </div>
                                                                ))}
                                                            </motion.div>
                                                        )}
                                                    </AnimatePresence>
                                                </div>
                                            );
                                        })}
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

// Formatting utilities
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

const formatDateWithTime = (isoString) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleString('en-US', { 
        day: 'numeric', 
        month: 'short', 
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
};

const formatDateWithTimeShort = (isoString) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleString('en-US', { 
        day: 'numeric', 
        month: 'short',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
};

const formatTimeOnly = (isoString) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
    });
};

export default DashaPage;
