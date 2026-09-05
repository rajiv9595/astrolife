import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/ui/Navbar';
import VedicCard from '../components/ui/VedicCard';
import SouthIndianChart from '../components/charts/SouthIndianChart';
import NorthIndianChart from '../components/charts/NorthIndianChart';
import DashaTimeline from '../components/charts/DashaTimeline';
import AIAstrologer from '../components/ai/AIAstrologer';
import { authService } from '../services/authService';
import { astroService } from '../services/astroService';
import { User, MapPin, Calendar, Clock, RefreshCw, Star } from 'lucide-react';
import { toast } from 'react-toastify';

const DashboardPage = () => {
    const navigate = useNavigate();
    const [user, setUser] = useState(null);
    const [chartData, setChartData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [activeChart, setActiveChart] = useState('D1'); // D1, D9, D10
    const [chartStyle, setChartStyle] = useState('south'); // 'south' or 'north'

    useEffect(() => {
        const fetchData = async () => {
            try {
                const currentUser = await authService.getCurrentUser();
                setUser(currentUser);

                // Get params for chart
                // Get params for chart
                const params = await authService.getChartDataParams();

                if (!params) {
                    toast.info("Please complete your birth details to view your chart.");
                    navigate('/tools/info');
                    return;
                }

                const data = await astroService.computeChart(params);
                setChartData(data);
            } catch (err) {
                console.error("Failed to compute chart", err);
                if (err.response && (err.response.status === 401 || err.response.status === 403)) {
                    toast.error("Session expired. Please login again.");
                    navigate('/auth');
                } else if (err.response && err.response.status >= 500) {
                    toast.error("Server calculation error. Please try again later.");
                } else if (!err.response) {
                    toast.error("Network connection error. Please check your internet.");
                } else {
                    toast.error("Failed to load chart: " + (err.message || "Unknown error"));
                }
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [navigate]);

    if (loading) {
        return (
            <div className="min-h-screen bg-vedic-cream flex items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-16 h-16 border-4 border-vedic-orange border-t-transparent rounded-full animate-spin" />
                    <p className="text-vedic-blue font-bold animate-pulse">Consulting the Stars...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-vedic-cream pb-20">
            <Navbar />

            <main className="max-w-7xl mx-auto px-4 sm:px-6 pt-12 space-y-8">

                {/* Top Section: Profile & Quick Stats - Now in clean white cards */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Profile Card */}
                    <VedicCard className="p-8 flex flex-col gap-6 text-center lg:text-left">
                        <div className="flex flex-col lg:flex-row items-center gap-6">
                            <div className="w-20 h-20 rounded-full bg-vedic-orange flex items-center justify-center text-3xl font-serif font-bold text-white shadow-lg">
                                {user?.name?.charAt(0)}
                            </div>
                            <div>
                                <h2 className="text-2xl font-serif font-bold text-vedic-blue">{user?.name}</h2>
                                <p className="text-stone-500 uppercase text-xs tracking-wider">Premium Member</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 gap-3 mt-2 pt-6 border-t border-stone-100">
                            <div className="flex items-center gap-3 text-sm text-stone-600">
                                <Calendar size={16} className="text-vedic-gold" />
                                <strong>DOB:</strong> {user?.date_of_birth}
                            </div>
                            <div className="flex items-center gap-3 text-sm text-stone-600">
                                <Clock size={16} className="text-vedic-gold" />
                                <strong>Time:</strong> {user?.time_of_birth}
                            </div>
                            <div className="flex items-center gap-3 text-sm text-stone-600">
                                <MapPin size={16} className="text-vedic-gold" />
                                <strong>Place:</strong> {user?.location}
                            </div>
                        </div>
                    </VedicCard>

                    {/* Key Astrological Stats */}
                    <VedicCard className="lg:col-span-2 p-8 flex flex-wrap items-center justify-around gap-8 bg-white/50">
                        <StatItem label="Ascendant" value={chartData?.ascendant?.sign} sub={chartData?.ascendant?.nakshatra?.nakshatra} />
                        <StatItem label="Moon Sign" value={chartData?.moon_sign} sub={chartData?.nakshatra_of_moon?.nakshatra} />
                        <StatItem label="Current Dasha" value={getActiveDasha(chartData?.vimshottari)} highlight />
                        <StatItem label="Lucky Gem" value={chartData?.lucky_factors?.lucky_gemstone} />
                    </VedicCard>
                </div>

                {/* Main Chart Area */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 h-full">

                    {/* Chart Visualizer */}
                    <div className="lg:col-span-2 flex flex-col">
                        <div className="flex flex-col sm:flex-row justify-between items-center gap-4 mb-6">
                            <div className="flex gap-2 bg-white p-2 rounded-lg shadow-sm w-fit border border-stone-100">
                                {['D1', 'D9', 'D10'].map(type => (
                                    <button
                                        key={type}
                                        onClick={() => setActiveChart(type)}
                                        className={`px-6 py-2 rounded-md text-sm font-bold transition-colors ${activeChart === type ? 'bg-vedic-orange text-white shadow-md' : 'text-stone-500 hover:text-vedic-blue hover:bg-stone-50'}`}
                                    >
                                        {type === 'D1' ? 'Lagna (D1)' : type === 'D9' ? 'Navamsa (D9)' : 'Dashamsha (D10)'}
                                    </button>
                                ))}
                            </div>
                            
                            <div className="flex gap-2 bg-white p-1 rounded-lg w-fit border border-stone-100 shadow-xs">
                                <button
                                    onClick={() => setChartStyle('south')}
                                    className={`px-3 py-1.5 rounded-md text-xs font-bold transition-colors ${chartStyle === 'south' ? 'bg-vedic-orange text-white shadow-sm font-extrabold' : 'text-stone-500 hover:bg-stone-50'}`}
                                >
                                    South Indian
                                </button>
                                <button
                                    onClick={() => setChartStyle('north')}
                                    className={`px-3 py-1.5 rounded-md text-xs font-bold transition-colors ${chartStyle === 'north' ? 'bg-vedic-orange text-white shadow-sm font-extrabold' : 'text-stone-500 hover:bg-stone-50'}`}
                                >
                                    North Indian
                                </button>
                            </div>
                        </div>

                        <VedicCard className="p-4 sm:p-8 flex-1 flex items-center justify-center bg-white border-2 border-vedic-gold/20">
                            {chartStyle === 'south' ? (
                                <SouthIndianChart
                                    chartData={getChartDataByType(chartData, activeChart)}
                                    title={activeChart === 'D1' ? 'Janma Kundli (D1)' : activeChart === 'D9' ? 'Navamsa Chart (D9)' : 'Dashamsha Chart (D10)'}
                                />
                            ) : (
                                <NorthIndianChart
                                    chartData={getChartDataByType(chartData, activeChart)}
                                    title={activeChart === 'D1' ? 'Janma Kundli (D1)' : activeChart === 'D9' ? 'Navamsa Chart (D9)' : 'Dashamsha Chart (D10)'}
                                />
                            )}
                        </VedicCard>
                    </div>

                    {/* Right Panel: Important Yogas */}
                    <div className="flex flex-col">
                        {/* Spacer to align with Chart Card (compensating for the buttons on left) */}
                        <div className="flex gap-2 mb-6 p-2 invisible">
                            <button className="px-6 py-2 text-sm font-bold opacity-0">Spacer</button>
                        </div>

                        <VedicCard className="p-0 max-h-[600px] overflow-y-auto custom-scrollbar bg-white flex flex-col">
                            <div className="p-6 bg-vedic-blue text-white sticky top-0 z-10 shrink-0">
                                <h3 className="text-lg font-serif font-bold">Important Yogas</h3>
                                <p className="text-xs text-stone-300 opacity-80">Special Planetary Combinations</p>
                            </div>
                            <div className="divide-y divide-stone-100 flex-1">
                                {chartData?.yogas && chartData.yogas.filter(y => y.status === 'STRONG' || y.status === 'ACTIVE').length > 0 ? (
                                    chartData.yogas.filter(y => y.status === 'STRONG' || y.status === 'ACTIVE').map((yoga, idx) => (
                                        <div key={idx} className="p-4 hover:bg-stone-50 transition-colors">
                                            <div className="flex items-start gap-3">
                                                <div className="w-8 h-8 rounded-full bg-vedic-orange/10 flex items-center justify-center text-vedic-orange shrink-0 mt-1">
                                                    <Star size={16} fill="currentColor" />
                                                </div>
                                                <div>
                                                    <h4 className="font-bold text-vedic-blue text-sm">{yoga.name}</h4>
                                                    <p className="text-xs text-stone-600 mt-1 leading-relaxed">{yoga.description}</p>
                                                    {/* <div className="mt-2 text-[10px] text-stone-400 font-mono bg-stone-100 inline-block px-2 py-1 rounded">
                                                        Score: {yoga.score?.toFixed(1) || 'N/A'}
                                                    </div> */}
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                ) : (
                                    <div className="p-8 text-center text-stone-500">
                                        <div className="mb-2">✨</div>
                                        <p className="text-sm">No major yogas detected in this chart view.</p>
                                    </div>
                                )}
                            </div>
                        </VedicCard>
                    </div>

                </div>

                {/* Bottom Timeline */}
                <DashaTimeline vimshottari={chartData?.vimshottari} />

            </main>

            {/* AI Assistant Overlay */}
            {chartData && <AIAstrologer chartData={chartData} />}
        </div>
    );
};

// Helpers
const StatItem = ({ label, value, sub, highlight }) => (
    <div className="text-center p-4">
        <div className="text-xs text-stone-400 font-bold uppercase tracking-wider mb-2">{label}</div>
        <div className={`text-xl font-serif font-bold ${highlight ? 'text-vedic-orange' : 'text-vedic-blue'}`}>
            {value || '--'}
        </div>
        {sub && <div className="text-xs text-vedic-muted font-medium mt-1">{sub}</div>}
    </div>
);

const getActiveDasha = (vim) => {
    if (!vim?.timeline) return "Unknown";
    const current = vim.timeline.find(d => d.is_current);
    return current ? `${current.lord} Mahadasha` : "Unknown";
};

const getChartDataByType = (fullData, type) => {
    if (!fullData) return {};
    const vKey = type.toLowerCase();
    if (fullData.vargas && fullData.vargas[vKey]) {
        const vData = fullData.vargas[vKey];
        const transformedPlanets = {};
        Object.entries(vData).forEach(([name, data]) => {
            if (name.startsWith('_') || name === 'planets') return;
            transformedPlanets[name] = { 
                ...data, 
                sign_manual: data[`${vKey}_sign`], 
                degree: data[`${vKey}_longitude`] 
            };
        });
        return { 
            ...fullData, 
            planets: transformedPlanets, 
            ascendant: vData._ascendant || { sign: 'Aries' },
            whole_sign_houses: vData._houses ? vData._houses.reduce((acc, h) => {
                acc[`house_${h.house}`] = { sign: h.sign, start_deg_sidereal: (h.sign_num - 1) * 30.0, end_deg_sidereal: h.sign_num * 30.0 };
                return acc;
            }, {}) : fullData.whole_sign_houses
        };
    }
    return fullData;
};

const getPlanetColor = (name) => {
    // Returning text/bg colors suitable for light mode
    switch (name) {
        case 'Sun': return 'bg-orange-100 text-orange-700';
        case 'Moon': return 'bg-stone-100 text-stone-700';
        case 'Mars': return 'bg-red-100 text-red-700';
        case 'Mercury': return 'bg-green-100 text-green-700';
        case 'Jupiter': return 'bg-yellow-100 text-yellow-700';
        case 'Venus': return 'bg-pink-100 text-pink-700';
        case 'Saturn': return 'bg-blue-100 text-blue-700';
        case 'Rahu': return 'bg-stone-800 text-stone-200';
        case 'Ketu': return 'bg-stone-600 text-stone-100';
        default: return 'bg-purple-100 text-purple-700';
    }
};

export default DashboardPage;
