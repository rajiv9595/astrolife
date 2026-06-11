import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Navbar from '../components/ui/Navbar';
import SouthIndianChart from '../components/charts/SouthIndianChart';
import NorthIndianChart from '../components/charts/NorthIndianChart';
import { astroService } from '../services/astroService';
import { Lock, ChevronRight, Share2, Download } from 'lucide-react';
import { motion } from 'framer-motion';

const GuestKundliPage = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const [chartData, setChartData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('D1');
    const [chartStyle, setChartStyle] = useState('south'); // 'south' or 'north'
    const { params, name } = location.state || {};

    useEffect(() => {
        if (!params) {
            navigate('/');
            return;
        }

        const fetchChart = async () => {
            try {
                const data = await astroService.computeChart(params);
                setChartData(data);
            } catch (err) {
                console.error(err);
                // Handle error
            } finally {
                setLoading(false);
            }
        };

        fetchChart();
    }, [params, navigate]);

    if (loading) {
        return (
            <div className="min-h-screen bg-vedic-cream flex items-center justify-center">
                <div className="w-16 h-16 border-4 border-vedic-orange border-t-transparent rounded-full animate-spin"></div>
            </div>
        );
    }

    if (!chartData) return null;

    return (
        <div className="min-h-screen bg-vedic-cream pb-20">
            <Navbar />

            <div className="max-w-7xl mx-auto px-6 py-12">

                {/* Header */}
                <div className="flex flex-col md:flex-row justify-between items-end mb-8 border-b border-stone-200 pb-6">
                    <div>
                        <div className="flex items-center gap-2 text-vedic-orange text-xs font-bold uppercase tracking-widest mb-2">
                            <span>Free Report</span>
                        </div>
                        <h1 className="text-3xl font-serif font-bold text-vedic-blue">
                            Kundli for {name || 'Guest'}
                        </h1>
                        <p className="text-stone-500 mt-2 text-sm">
                            {new Date().toLocaleDateString()} • {params?.lat?.toFixed(2)}°N, {params?.lon?.toFixed(2)}°E
                        </p>
                    </div>

                    <button
                        onClick={() => navigate('/auth?mode=signup')}
                        className="mt-4 md:mt-0 px-6 py-3 bg-vedic-orange text-white rounded-full font-bold shadow-lg shadow-orange-200 hover:shadow-xl hover:-translate-y-1 transition-all flex items-center gap-2"
                    >
                        <span>Save Profile & Get Full Report</span> <ChevronRight size={16} />
                    </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                    {/* Main Chart Area */}
                    <div className="lg:col-span-2 space-y-8">

                        {/* Chart Type Tabs and Style Toggle */}
                        <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
                            <div className="bg-white p-2 rounded-xl shadow-sm inline-flex gap-2 border border-stone-100">
                                {['D1', 'D9', 'D10'].map(type => (
                                    <button
                                        key={type}
                                        onClick={() => setActiveTab(type)}
                                        className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === type
                                                ? 'bg-vedic-blue text-white shadow-md'
                                                : 'text-stone-500 hover:bg-stone-50'
                                            }`}
                                    >
                                        {type === 'D1' ? 'Lagna (D1)' : type === 'D9' ? 'Navamsa (D9)' : 'Dasamsa (D10)'}
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

                        {/* Chart Display */}
                        <motion.div
                            key={activeTab}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="bg-white rounded-2xl p-8 shadow-vedic border border-stone-100 relative overflow-hidden"
                        >
                            {/* Watermark for guest */}
                            <div className="absolute inset-0 flex items-center justify-center opacity-[0.03] pointer-events-none">
                                <div className="text-9xl font-serif font-bold text-vedic-blue rotate-[-15deg]">LifePath</div>
                            </div>

                            <div className="flex justify-center">
                                <div className="w-full max-w-md aspect-square">
                                    {chartStyle === 'south' ? (
                                        <SouthIndianChart
                                            chartData={getChartDataByType(chartData, activeTab)}
                                            title={activeTab === 'D1' ? 'Lagna (D1)' : activeTab === 'D9' ? 'Navamsa (D9)' : 'Dasamsa (D10)'}
                                        />
                                    ) : (
                                        <NorthIndianChart
                                            chartData={getChartDataByType(chartData, activeTab)}
                                            title={activeTab === 'D1' ? 'Lagna (D1)' : activeTab === 'D9' ? 'Navamsa (D9)' : 'Dasamsa (D10)'}
                                        />
                                    )}
                                </div>
                            </div>
                        </motion.div>

                        {/* Planet Details Table */}
                        <div className="bg-white rounded-2xl p-6 shadow-sm border border-stone-100">
                            <h3 className="font-bold text-vedic-blue mb-4">Planetary Positions & Star Lords</h3>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm text-left border-collapse">
                                    <thead className="bg-stone-50 text-stone-500 font-bold uppercase text-xs border-b border-stone-200">
                                        <tr>
                                            <th className="p-3 rounded-l-lg">Planet</th>
                                            <th className="p-3">Sign</th>
                                            <th className="p-3">Degree</th>
                                            <th className="p-3 text-center">House</th>
                                            <th className="p-3">Nakshatra</th>
                                            <th className="p-3 rounded-r-lg">Star Lord</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-stone-100">
                                        {Object.entries(chartData.planets).map(([planet, details]) => {
                                            const degVal = details.degree !== undefined ? details.degree : (details.longitude !== undefined ? details.longitude : 0);
                                            const pSign = details.sign_manual || details.sign;
                                            
                                            const SIGNS_LIST = [
                                                "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                                                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
                                            ];
                                            
                                            let houseNum = "";
                                            if (chartData.ascendant?.sign && pSign) {
                                                try {
                                                    const ascIdx = SIGNS_LIST.indexOf(chartData.ascendant.sign);
                                                    const pIdx = SIGNS_LIST.indexOf(pSign);
                                                    if (ascIdx !== -1 && pIdx !== -1) {
                                                        houseNum = ((pIdx - ascIdx + 12) % 12) + 1;
                                                    }
                                                } catch (e) {}
                                            }
                                            
                                            return (
                                                <tr key={planet} className="hover:bg-stone-50/50">
                                                    <td className="p-3 font-semibold text-vedic-blue flex items-center gap-1">
                                                        {planet}
                                                        {details.retrograde && <span className="text-[8px] px-1 bg-red-50 text-red-500 border border-red-100 rounded font-bold">R</span>}
                                                        {details.combust && <span className="text-[8px] px-1 bg-orange-50 text-orange-500 border border-orange-100 rounded font-bold">C</span>}
                                                    </td>
                                                    <td className="p-3 text-stone-600">{pSign || "--"}</td>
                                                    <td className="p-3 text-stone-500 font-mono text-xs">
                                                        {Math.floor(degVal)}°{Math.floor((degVal % 1) * 60)}'
                                                    </td>
                                                    <td className="p-3 text-stone-600 text-center font-bold">{houseNum || "--"}</td>
                                                    <td className="p-3 text-stone-500 text-xs">
                                                        {details.nakshatra?.nakshatra ? `${details.nakshatra.nakshatra} (Pada ${details.nakshatra.pada})` : "--"}
                                                    </td>
                                                    <td className="p-3 text-stone-600 font-medium">{details.star_lord || "--"}</td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                    </div>

                    {/* Locked Features Sidebar */}
                    <div className="space-y-6">
                        <LockedCard title="Auspicious Yogas" desc="Discover 50+ Raja Yogas and their effects on your life." />
                        <LockedCard title="Vimshottari Dasha" desc="Detailed timeline of your life events and periods." />
                        <LockedCard title="Gemstone Remedies" desc="Personalized recommendations to boost your luck." />
                        <LockedCard title="Life Predictions" desc="AI-driven analysis of your career, marriage and health." />

                        <div className="bg-gradient-to-br from-vedic-orange to-orange-600 rounded-2xl p-8 text-white text-center shadow-xl relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-16 bg-white/10 rounded-full blur-2xl -mr-10 -mt-10"></div>
                            <h3 className="text-2xl font-serif font-bold mb-3">Unlock Everything</h3>
                            <p className="text-white/90 mb-6 text-sm">
                                Create a free account to access detailed predictions, save your profile, and talk to astrologers.
                            </p>
                            <button
                                onClick={() => navigate('/auth?mode=signup')}
                                className="w-full bg-white text-vedic-orange font-bold py-3.5 rounded-xl hover:bg-stone-50 transition-colors shadow-lg"
                            >
                                Create Free Account
                            </button>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
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

const LockedCard = ({ title, desc }) => (
    <div className="bg-white rounded-xl p-6 border border-stone-100 shadow-sm relative overflow-hidden group">
        <div className="absolute inset-0 bg-stone-50/80 backdrop-blur-[1px] flex items-center justify-center z-10 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            <div className="bg-white text-vedic-blue text-xs font-bold px-4 py-2 rounded-full shadow-md flex items-center gap-2">
                <Lock size={12} /> Login to Unlock
            </div>
        </div>
        <div className="flex items-start justify-between mb-2 opacity-60 filter blur-[0.5px]">
            <h4 className="font-bold text-stone-700">{title}</h4>
            <Lock size={16} className="text-stone-400" />
        </div>
        <p className="text-sm text-stone-400 opacity-60 filter blur-[0.5px]">{desc}</p>
    </div>
);

export default GuestKundliPage;
