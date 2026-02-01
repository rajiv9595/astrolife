import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../../components/ui/Navbar';
import VedicCard from '../../components/ui/VedicCard';
import SouthIndianChart from '../../components/charts/SouthIndianChart';
import DashaTimeline from '../../components/charts/DashaTimeline';
import AIAstrologer from '../../components/ai/AIAstrologer';
import { authService } from '../../services/authService';
import { astroService } from '../../services/astroService';
import { familyService } from '../../services/familyService';
import FamilyMemberModal from '../../components/features/horoscope/FamilyMemberModal';
import {
    User, MapPin, Calendar, Clock, ChevronDown, Plus,
    Edit2, Trash2, RefreshCw, Star, Users, Check
} from 'lucide-react';
import { toast } from 'react-toastify';
import { motion, AnimatePresence } from 'framer-motion';

const HoroscopePage = () => {
    const navigate = useNavigate();
    const [currentUser, setCurrentUser] = useState(null);
    const [familyMembers, setFamilyMembers] = useState([]);

    // Selection State
    // selectedId: 'me' for current user, or integer ID for family member
    const [selectedId, setSelectedId] = useState('me');
    const [activeChart, setActiveChart] = useState('D1');
    const [chartData, setChartData] = useState(null);
    const [loading, setLoading] = useState(false);

    // Dropdown State
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const dropdownRef = useRef(null);

    // Modal State
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingMember, setEditingMember] = useState(null);

    // Initial Load
    useEffect(() => {
        const init = async () => {
            try {
                const user = await authService.getCurrentUser();
                setCurrentUser(user);

                const members = await familyService.getAll();
                setFamilyMembers(members);

                // Auto-load current user's chart
                loadChartFor('me', user);
            } catch (err) {
                console.error(err);
                toast.error("Please login to access Horoscope.");
                navigate('/auth');
            }
        };
        init();

        // Close dropdown when clicking outside
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsDropdownOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [navigate]);

    const getSelectedPerson = () => {
        if (selectedId === 'me') return currentUser;
        return familyMembers.find(m => m.id === selectedId);
    };

    const loadChartFor = async (id, personObj = null) => {
        setLoading(true);
        try {
            let person = personObj;
            if (!person) {
                if (id === 'me') person = currentUser;
                else person = familyMembers.find(m => m.id === id);
            }

            if (!person) return;
            if (!person.date_of_birth || !person.time_of_birth) {
                setChartData(null);
                setLoading(false);
                return;
            }

            // Construct Params
            const dobParts = person.date_of_birth.split("-");
            const timeParts = person.time_of_birth.split(":") || ["00", "00"];

            const params = {
                year: parseInt(dobParts[0]),
                month: parseInt(dobParts[1]),
                day: parseInt(dobParts[2]),
                hour: parseInt(timeParts[0]),
                minute: parseInt(timeParts[1]),
                second: 0,
                tz: person.timezone || "Asia/Kolkata",
                lat: person.latitude || 0.0,
                lon: person.longitude || 0.0,
                // planets: All by default in backend
            };

            const data = await astroService.computeChart(params);
            setChartData(data);
            setSelectedId(id);
        } catch (err) {
            console.error(err);
            toast.error("Failed to load chart.");
        } finally {
            setLoading(false);
        }
    };

    const handleAddMember = async (data) => {
        try {
            const newMember = await familyService.add(data);
            setFamilyMembers([...familyMembers, newMember]);
            setIsModalOpen(false);
            toast.success(`${newMember.name} added successfully`);

            // Switch to new member
            loadChartFor(newMember.id, newMember);
        } catch (err) {
            console.error(err);
            toast.error("Failed to add member");
        }
    };

    const handleUpdateMember = async (data) => {
        try {
            const updated = await familyService.update(editingMember.id, data);
            setFamilyMembers(members => members.map(m => m.id === updated.id ? updated : m));
            setIsModalOpen(false);
            setEditingMember(null);
            toast.success("Updated successfully");

            if (selectedId === updated.id) {
                loadChartFor(updated.id, updated);
            }
        } catch (err) {
            console.error(err);
            toast.error("Failed to update");
        }
    };

    const handleDeleteMember = async (e, id) => {
        e.stopPropagation();
        if (!window.confirm("Are you sure you want to remove this person?")) return;

        try {
            await familyService.delete(id);
            setFamilyMembers(members => members.filter(m => m.id !== id));
            toast.success("Removed successfully");
            if (selectedId === id) {
                loadChartFor('me', currentUser);
            }
        } catch (err) {
            console.error(err);
            toast.error("Failed to delete");
        }
    };

    const openEditModal = (e, member) => {
        e.stopPropagation();
        setEditingMember(member);
        setIsModalOpen(true);
        setIsDropdownOpen(false);
    };

    // --- Helpers for Display ---
    const person = getSelectedPerson();

    const getChartDataByType = (fullData, type) => {
        if (!fullData) return {};
        if (type === 'D1') return fullData;
        if (type === 'D9' && fullData.d9) {
            const transformedPlanets = {};
            Object.entries(fullData.d9).forEach(([name, data]) => {
                if (name.startsWith('_')) return;
                transformedPlanets[name] = { ...data, sign_manual: data.d9_sign, degree: data.d9_longitude };
            });
            return { ...fullData, planets: transformedPlanets, ascendant: fullData.d9._ascendant || { sign: 'Aries' } };
        }
        if (type === 'D10' && fullData.d10) {
            const transformedPlanets = {};
            Object.entries(fullData.d10).forEach(([name, data]) => {
                if (name.startsWith('_')) return;
                transformedPlanets[name] = { ...data, sign_manual: data.d10_sign, degree: data.d10_longitude };
            });
            return { ...fullData, planets: transformedPlanets, ascendant: fullData.d10._ascendant || { sign: 'Aries' } };
        }
        return fullData;
    };

    const getActiveDasha = (vim) => {
        if (!vim?.timeline) return "Unknown";
        const current = vim.timeline.find(d => d.is_current);
        return current ? `${current.lord} Mahadasha` : "Unknown";
    };

    return (
        <div className="min-h-screen bg-vedic-cream pb-20">
            {/* Custom Navbar Area with Selector embedded or separate? */}
            {/* Sticking to standard layout with Navbar */}
            <Navbar />

            <div className="bg-white border-b border-stone-100 shadow-sm sticky top-20 z-40">
                <div className="max-w-7xl mx-auto px-4 py-4 flex flex-col md:flex-row items-center justify-between gap-4">

                    <div className="flex items-center gap-4 w-full md:w-auto">
                        <div className="w-10 h-10 rounded-full bg-vedic-orange/10 flex items-center justify-center text-vedic-orange shrink-0">
                            <Star size={20} fill="currentColor" />
                        </div>
                        <div>
                            <h1 className="text-xl font-serif font-bold text-vedic-blue leading-none">Horoscope</h1>
                            <p className="text-xs text-stone-500 mt-1">Detailed Analysis & Predictions</p>
                        </div>
                    </div>

                    {/* Person Selector */}
                    <div className="relative w-full md:w-80" ref={dropdownRef}>
                        <label className="text-xs font-bold text-stone-400 uppercase mb-1 block">Select Person</label>
                        <button
                            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                            className="w-full flex items-center justify-between bg-white border border-stone-200 rounded-lg px-4 py-2.5 hover:border-vedic-orange transition-colors text-left"
                        >
                            <span className="font-medium text-vedic-blue truncate">
                                {person ? (selectedId === 'me' ? `${person.name} (Result)` : person.name) : 'Select Person...'}
                            </span>
                            <ChevronDown size={16} className={`text-stone-400 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
                        </button>

                        <AnimatePresence>
                            {isDropdownOpen && (
                                <motion.div
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: 10 }}
                                    className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-xl border border-stone-100 overflow-hidden z-50 py-2"
                                >
                                    {/* Search input could go here if needed */}

                                    <div className="max-h-60 overflow-y-auto custom-scrollbar">
                                        <div
                                            onClick={() => { loadChartFor('me', currentUser); setIsDropdownOpen(false); }}
                                            className={`px-4 py-3 flex items-center justify-between hover:bg-stone-50 cursor-pointer ${selectedId === 'me' ? 'bg-vedic-orange/5' : ''}`}
                                        >
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 rounded-full bg-stone-100 flex items-center justify-center text-stone-600 font-bold text-xs">
                                                    ME
                                                </div>
                                                <div>
                                                    <div className="font-bold text-sm text-vedic-blue">{currentUser?.name}</div>
                                                    <div className="text-xs text-stone-500">My Profile</div>
                                                </div>
                                            </div>
                                            {selectedId === 'me' && <Check size={16} className="text-vedic-orange" />}
                                        </div>

                                        {familyMembers.length > 0 && <div className="px-4 py-2 text-[10px] font-bold text-stone-400 uppercase tracking-wider">Family Members</div>}

                                        {familyMembers.map(member => (
                                            <div
                                                key={member.id}
                                                className={`px-4 py-3 flex items-center justify-between hover:bg-stone-50 cursor-pointer group ${selectedId === member.id ? 'bg-vedic-orange/5' : ''}`}
                                                onClick={() => { loadChartFor(member.id, member); setIsDropdownOpen(false); }}
                                            >
                                                <div className="flex items-center gap-3">
                                                    <div className="w-8 h-8 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-600 font-bold text-xs">
                                                        {member.name.charAt(0)}
                                                    </div>
                                                    <div>
                                                        <div className="font-bold text-sm text-vedic-blue">{member.name}</div>
                                                        <div className="text-xs text-stone-500">{member.relationship} • {member.date_of_birth?.split('-')[0]}</div>
                                                    </div>
                                                </div>

                                                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                    {selectedId === member.id && <Check size={16} className="text-vedic-orange mr-2" />}
                                                    <button onClick={(e) => openEditModal(e, member)} className="p-1.5 hover:bg-stone-200 rounded text-stone-500">
                                                        <Edit2 size={14} />
                                                    </button>
                                                    <button onClick={(e) => handleDeleteMember(e, member.id)} className="p-1.5 hover:bg-red-50 text-red-400 hover:text-red-500 rounded">
                                                        <Trash2 size={14} />
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>

                                    <div className="border-t border-stone-100 mt-2 pt-2 px-2">
                                        <button
                                            onClick={() => { setEditingMember(null); setIsModalOpen(true); setIsDropdownOpen(false); }}
                                            className="w-full flex items-center justify-center gap-2 py-2 text-sm font-bold text-vedic-orange hover:bg-vedic-orange/5 rounded-lg transition-colors"
                                        >
                                            <Plus size={16} /> Add Person
                                        </button>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>
            </div>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 pt-8 space-y-8">
                {/* Person Info Bar */}
                {person && (
                    <div className="flex flex-wrap items-center gap-4 text-xs text-stone-500 px-2">
                        <div className="flex items-center gap-1 bg-white px-3 py-1 rounded-full border border-stone-200">
                            <Calendar size={12} /> {person.date_of_birth}
                        </div>
                        <div className="flex items-center gap-1 bg-white px-3 py-1 rounded-full border border-stone-200">
                            <Clock size={12} /> {person.time_of_birth}
                        </div>
                        <div className="flex items-center gap-1 bg-white px-3 py-1 rounded-full border border-stone-200">
                            <MapPin size={12} /> {person.location}
                        </div>
                    </div>
                )}

                {loading ? (
                    <div className="min-h-[400px] flex items-center justify-center">
                        <div className="flex flex-col items-center gap-4">
                            <RefreshCw className="w-8 h-8 text-vedic-orange animate-spin" />
                            <p className="text-stone-500 font-medium">Computing Chart...</p>
                        </div>
                    </div>
                ) : chartData ? (
                    <>
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                            {/* Key Stats */}
                            <VedicCard className="lg:col-span-3 p-6 flex flex-wrap items-center justify-around gap-8 bg-white">
                                <StatItem label="Ascendant" value={chartData.ascendant?.sign} sub={chartData.ascendant?.nakshatra?.nakshatra} />
                                <StatItem label="Moon Sign" value={chartData.moon_sign} sub={chartData.nakshatra_of_moon?.nakshatra} />
                                <StatItem label="Current Dasha" value={getActiveDasha(chartData.vimshottari)} highlight />
                            </VedicCard>

                            {/* Charts Visualization */}
                            <div className="lg:col-span-2 space-y-6">
                                <div className="flex gap-2 bg-white p-1 rounded-lg w-fit border border-stone-100">
                                    {['D1', 'D9', 'D10'].map(type => (
                                        <button
                                            key={type}
                                            onClick={() => setActiveChart(type)}
                                            className={`px-4 py-1.5 rounded-md text-xs font-bold transition-colors ${activeChart === type ? 'bg-vedic-blue text-white' : 'text-stone-500 hover:bg-stone-50'}`}
                                        >
                                            {type} Chart
                                        </button>
                                    ))}
                                </div>
                                <VedicCard className="p-4 bg-white flex justify-center">
                                    <SouthIndianChart
                                        chartData={getChartDataByType(chartData, activeChart)}
                                        title={`${activeChart} - ${person.name}`}
                                    />
                                </VedicCard>

                                <DashaTimeline vimshottari={chartData.vimshottari} />
                            </div>

                            {/* Planetary Details */}
                            <div className="space-y-6">
                                <VedicCard className="p-0 overflow-hidden bg-white">
                                    <div className="bg-vedic-blue px-4 py-3">
                                        <h3 className="text-white font-bold text-sm">Planetary Positions</h3>
                                    </div>
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm">
                                            <thead className="bg-stone-50 text-stone-500 text-xs uppercase font-bold text-left">
                                                <tr>
                                                    <th className="px-4 py-2">Planet</th>
                                                    <th className="px-4 py-2">Sign</th>
                                                    <th className="px-4 py-2">Deg</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-stone-100">
                                                {Object.entries(chartData.planets).map(([key, p]) => (
                                                    <tr key={key} className="hover:bg-vedic-cream/30">
                                                        <td className="px-4 py-2 font-medium text-vedic-blue">{key}</td>
                                                        <td className="px-4 py-2 text-stone-600">{p.sign_manual || p.sign}</td>
                                                        <td className="px-4 py-2 text-stone-500 font-mono text-xs">{Math.floor(p.degree)}°{Math.floor((p.degree % 1) * 60)}'</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </VedicCard>
                            </div>
                        </div>
                    </>
                ) : (
                    <div className="text-center py-20 text-stone-400">
                        <Users size={48} className="mx-auto mb-4 opacity-20" />
                        <p>Select a person to view horoscope</p>
                    </div>
                )}
            </main>

            {/* AI Assistant */}
            {chartData && <AIAstrologer chartData={chartData} />}

            {/* Modal */}
            <FamilyMemberModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSubmit={editingMember ? handleUpdateMember : handleAddMember}
                initialData={editingMember}
            />
        </div>
    );
};

const StatItem = ({ label, value, sub, highlight }) => (
    <div className="text-center">
        <div className="text-[10px] text-stone-400 font-bold uppercase tracking-wider mb-1">{label}</div>
        <div className={`text-lg font-serif font-bold ${highlight ? 'text-vedic-orange' : 'text-vedic-blue'}`}>
            {value || '--'}
        </div>
        {sub && <div className="text-[10px] text-vedic-muted">{sub}</div>}
    </div>
);

export default HoroscopePage;
