import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/ui/Navbar';
import VedicCard from '../components/ui/VedicCard';
import { authService } from '../services/authService';
import { astroService } from '../services/astroService';
import { ArrowLeft } from 'lucide-react';
import { toast } from 'react-toastify';

const PlanetsPage = () => {
    const navigate = useNavigate();
    const [chartData, setChartData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [userName, setUserName] = useState('');

    useEffect(() => {
        const fetchChartData = async () => {
            try {
                // Get user details
                let currentUser = null;
                try {
                    currentUser = await authService.getCurrentUser();
                    if (currentUser) setUserName(currentUser.name);
                } catch (e) {
                    console.warn("Could not fetch user details", e);
                }

                // Check for cached chart data first
                const cachedData = localStorage.getItem('chartData');
                if (cachedData) {
                    setChartData(JSON.parse(cachedData));
                    setLoading(false);
                }

                // Verify or fetch fresh data
                const formData = await authService.getChartDataParams();
                if (!formData) {
                    toast.error("Please enter your birth details first.");
                    navigate('/enter-details');
                    return;
                }

                const data = await astroService.computeChart(formData);
                setChartData(data);
                localStorage.setItem('chartData', JSON.stringify(data));
                setLoading(false);

            } catch (err) {
                console.error("Error fetching chart data:", err);
                toast.error("Failed to load planetary positions.");
                setLoading(false);
            }
        };

        fetchChartData();
    }, [navigate]);

    const formatDMS = (decimalDeg) => {
        if (decimalDeg === undefined || decimalDeg === null || isNaN(decimalDeg)) return "-";
        const d = Math.floor(decimalDeg);
        const mFloat = (decimalDeg - d) * 60;
        const m = Math.floor(mFloat);
        const s = Math.round((mFloat - m) * 60);
        return `${d.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    };

    const getStatus = (data) => {
        const statuses = [];
        if (data.retrograde) statuses.push("(R)");
        if (data.combust) statuses.push("(C)");
        return statuses.length > 0 ? statuses.join(" ") : "-";
    };

    const getHouseNumber = (sign, houses) => {
        if (!houses) return "-";
        for (const [houseKey, houseData] of Object.entries(houses)) {
            if (houseData.sign === sign) {
                return houseKey.replace("house_", "");
            }
        }
        return "-";
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-vedic-cream flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-vedic-orange"></div>
            </div>
        );
    }

    // Prepare sorted list of planets for display
    const planetOrder = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"];
    const rows = [];

    if (chartData) {
        // Add planets in specific order
        planetOrder.forEach(pName => {
            if (chartData.planets[pName]) {
                rows.push({ name: pName, ...chartData.planets[pName] });
            }
        });

        // Add Ascendant at the end or beginning (User image shows it at end of table 1, start of table 2? No, both at end/start mixed. Let's put Ascendant at bottom as per image 1)
        if (chartData.ascendant) {
            rows.push({
                name: "Ascendant",
                sign_manual: chartData.ascendant.sign,
                degree_in_sign_manual: chartData.ascendant.deg_in_sign,
                nakshatra: chartData.ascendant.nakshatra,
                d9_sign: chartData.ascendant.d9_sign,
                d9_sign_lord: chartData.ascendant.d9_sign_lord,
                isAscendant: true
            });
        }
    }

    return (
        <div className="font-sans">

            <main className="max-w-6xl mx-auto py-4">
                {/* Header */}
                <div className="flex items-center gap-4 mb-8">
                    <div>
                        <h1 className="text-3xl font-serif font-bold text-vedic-blue">Planetary Positions</h1>
                        <p className="text-stone-500 text-sm mt-1">
                            Name: <span className="font-bold text-vedic-orange">{userName || "User"}</span>
                        </p>
                    </div>
                </div>

                {/* Table 1: Basic Positions */}
                <VedicCard className="mb-8 overflow-hidden p-0 bg-white">
                    <div className="bg-vedic-blue px-6 py-4 border-b border-white/10">
                        <h2 className="text-white font-serif font-bold text-lg">Planetary Positions</h2>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead className="bg-vedic-blue/5 text-vedic-blue font-bold uppercase text-xs tracking-wider">
                                <tr>
                                    <th className="px-6 py-4">Planet</th>
                                    <th className="px-6 py-4 text-center">Status</th>
                                    <th className="px-6 py-4">Sign</th>
                                    <th className="px-6 py-4 text-right">Degrees</th>
                                    <th className="px-6 py-4 text-center">House</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-stone-100">
                                {rows.map((row, idx) => (
                                    <tr key={idx} className="hover:bg-vedic-orange/5 transition-colors">
                                        <td className="px-6 py-4 font-bold text-vedic-blue">{row.name}</td>
                                        <td className="px-6 py-4 text-center text-stone-500 font-mono text-xs">
                                            {row.isAscendant ? '-' : getStatus(row)}
                                        </td>
                                        <td className="px-6 py-4 text-stone-700">{row.sign_manual}</td>
                                        <td className="px-6 py-4 text-right font-mono text-vedic-orange font-medium">
                                            {formatDMS(row.degree_in_sign_manual)}
                                        </td>
                                        <td className="px-6 py-4 text-center font-bold text-stone-700">
                                            {row.isAscendant ? '1' : getHouseNumber(row.sign_manual, chartData?.whole_sign_houses)}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </VedicCard>

                {/* Legend for Table 1 */}
                <div className="flex gap-6 justify-center text-xs text-stone-500 mb-12">
                    <span className="flex items-center gap-1"><strong className="text-vedic-blue">(R)</strong> = Retrograde</span>
                    <span className="flex items-center gap-1"><strong className="text-vedic-blue">(C)</strong> = Combust</span>
                </div>

                {/* Table 2: Nakshatra & Divisional Charts */}
                <VedicCard className="overflow-hidden p-0 bg-white">
                    <div className="bg-vedic-blue px-6 py-4 border-b border-white/10">
                        <h2 className="text-white font-serif font-bold text-lg">Nakshatra & Navamsa Details</h2>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead className="bg-vedic-blue/5 text-vedic-blue font-bold uppercase text-xs tracking-wider">
                                <tr>
                                    <th className="px-6 py-4">Planet</th>
                                    <th className="px-6 py-4">Nakshatra / Pada</th>
                                    <th className="px-6 py-4">Nakshatra Lord</th>
                                    <th className="px-6 py-4">Navamsa (D9)</th>
                                    <th className="px-6 py-4">Navamsa Lord</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-stone-100">
                                {rows.map((row, idx) => (
                                    <tr key={idx} className="hover:bg-vedic-orange/5 transition-colors">
                                        <td className="px-6 py-4 font-bold text-vedic-blue">{row.name}</td>
                                        <td className="px-6 py-4 text-stone-700">
                                            {row.nakshatra ? `${row.nakshatra.nakshatra}-${row.nakshatra.pada}` : '-'}
                                        </td>
                                        <td className="px-6 py-4 text-stone-600">
                                            {row.nakshatra?.lord || '-'}
                                        </td>
                                        <td className="px-6 py-4 text-stone-700">
                                            {row.d9_sign || '-'}
                                        </td>
                                        <td className="px-6 py-4 text-stone-600">
                                            {row.d9_sign_lord || '-'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </VedicCard>

            </main>
        </div>
    );
};

export default PlanetsPage;
