import React, { useState, useEffect } from 'react';
import Navbar from '../components/ui/Navbar';
import GlassCard from '../components/ui/GlassCard';
import Input from '../components/ui/Input';
import LocationInput from '../components/ui/LocationInput';
import CosmicButton from '../components/ui/CosmicButton';
import { astroService } from '../services/astroService';
import { Heart, Search, Award, ArrowLeft } from 'lucide-react';
import { motion } from 'framer-motion';

const MatchPage = () => {
    const [boyData, setBoyData] = useState(initialState);
    const [girlData, setGirlData] = useState(initialState);
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleMatch = async () => {
        setLoading(true);
        try {
            // Basic validation skipped for brevity
            const data = await astroService.matchCharts(formatParams(boyData), formatParams(girlData));
            setResult(data);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-vedic-cream pb-20">
            <Navbar />
            <div className="max-w-6xl mx-auto px-6 pt-24">
                <div className="text-center mb-12">
                    <h1 className="text-4xl font-serif font-bold text-vedic-blue mb-4">Cosmic Compatibility</h1>
                    <p className="text-stone-600">Analyze the spiritual and mental union of two souls.</p>
                </div>

                {!result ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8 relative">
                        {/* Divider */}
                        <div className="hidden md:flex absolute left-1/2 top-10 bottom-10 -translate-x-1/2 w-px bg-gradient-to-b from-transparent via-white/20 to-transparent z-0" />

                        <ProfileInput title="Boy's Details" data={boyData} setData={setBoyData} icon="♂" color="blue" />
                        <ProfileInput title="Girl's Details" data={girlData} setData={setGirlData} icon="♀" color="pink" />

                        <div className="md:col-span-2 flex justify-center mt-8 relative z-10">
                            <button
                                onClick={handleMatch}
                                disabled={loading}
                                className="bg-gradient-to-r from-vedic-orange to-red-500 text-white px-12 py-4 rounded-full font-bold text-lg shadow-xl hover:shadow-2xl hover:scale-105 transition-all duration-300 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {loading ? 'Aligning Stars...' : 'Calculate Compatibility'} <Heart className="ml-2 fill-white" />
                            </button>
                        </div>
                    </div>
                ) : (
                    <MatchResult result={result} onReset={() => setResult(null)} />
                )}
            </div>
        </div>
    );
};

const ProfileInput = ({ title, data, setData, icon, color }) => {

    const handleLocationSelect = (place) => {
        setData(prev => ({
            ...prev,
            lat: place.latitude,
            lon: place.longitude, // Corrected property name from fetched place
            location: place.display_name // Use full name
        }));
    };

    return (
        <div className="bg-white rounded-2xl p-6 md:p-8 shadow-xl border border-stone-200 z-10">
            <div className={`w-14 h-14 rounded-full flex items-center justify-center text-3xl mb-6 mx-auto shadow-md ${color === 'blue' ? 'bg-blue-100 text-blue-600' : 'bg-pink-100 text-pink-600'}`}>
                {icon}
            </div>
            <h3 className="text-xl font-serif font-bold text-center text-vedic-blue mb-6 border-b border-stone-100 pb-2">{title}</h3>
            <div className="space-y-5">
                <div className="space-y-1">
                    <label className="text-xs font-bold text-stone-500 uppercase tracking-wider block">Date of Birth</label>
                    <input
                        type="date"
                        className="w-full bg-stone-50 border border-stone-300 rounded-lg px-4 py-3 text-stone-900 focus:ring-2 focus:ring-vedic-orange focus:border-transparent outline-none transition-all font-medium"
                        value={data.dob}
                        onChange={e => setData({ ...data, dob: e.target.value })}
                    />
                </div>
                <div className="space-y-1">
                    <label className="text-xs font-bold text-stone-500 uppercase tracking-wider block">Time of Birth</label>
                    <input
                        type="time"
                        className="w-full bg-stone-50 border border-stone-300 rounded-lg px-4 py-3 text-stone-900 focus:ring-2 focus:ring-vedic-orange focus:border-transparent outline-none transition-all font-medium"
                        value={data.tob}
                        onChange={e => setData({ ...data, tob: e.target.value })}
                    />
                </div>

                <LocationInput
                    label="Place of Birth"
                    value={data.location}
                    onChange={(e) => setData({ ...data, location: e.target.value, lat: '', lon: '' })}
                    onLocationSelect={handleLocationSelect}
                    placeholder="City, Country"
                />
                {data.lat && <div className="text-xs text-green-600 font-medium flex items-center justify-end gap-1 mt-1">✓ Location Locked</div>}
            </div>
        </div>
    );
};

const MatchResult = ({ result, onReset }) => {
    const score = result.ashta_koota.total;
    const max = result.ashta_koota.max;
    const percentage = (score / max) * 100;

    return (
        <div className="flex flex-col items-center animate-fade-in w-full">
            <div className="w-full max-w-4xl mb-6 flex justify-start">
                <button
                    onClick={onReset}
                    className="flex items-center gap-2 text-stone-500 hover:text-vedic-orange transition-colors font-medium"
                >
                    <ArrowLeft size={20} /> Back to Search
                </button>
            </div>

            <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="relative w-64 h-64 flex items-center justify-center mb-8"
            >
                {/* Animated Rings */}
                <div className="absolute inset-0 border-4 border-stone-200 rounded-full" />
                <svg className="absolute inset-0 w-full h-full -rotate-90">
                    <circle cx="128" cy="128" r="120" stroke="rgba(0,0,0,0.1)" strokeWidth="8" fill="none" />
                    <motion.circle
                        cx="128" cy="128" r="120"
                        stroke={score > 18 ? "#4ADE80" : "#EF4444"}
                        strokeWidth="8" fill="none"
                        strokeDasharray="753"
                        initial={{ strokeDashoffset: 753 }}
                        animate={{ strokeDashoffset: 753 - (753 * percentage / 100) }}
                        transition={{ duration: 2, ease: "easeOut" }}
                    />
                </svg>
                <div className="text-center">
                    <div className="text-5xl font-bold text-vedic-blue mb-1">{score}</div>
                    <div className="text-stone-500 text-sm">out of {max}</div>
                </div>
            </motion.div>

            <h2 className="text-3xl font-serif text-vedic-blue mb-2">{result.ashta_koota.verdict}</h2>
            <p className="text-stone-600 mb-8 max-w-lg text-center">
                Based on Ashta Koota matching, the compatibility indicates a {result.ashta_koota.verdict.toLowerCase()} union.
            </p>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 w-full max-w-4xl mb-12">
                {result.ashta_koota.kootas.map((koota, idx) => (
                    <div key={idx} className="bg-white border border-stone-200 p-4 rounded-lg text-center shadow-sm">
                        <div className="text-xs text-stone-500 uppercase tracking-widest mb-1">{koota.koota}</div>
                        <div className="text-xl font-bold text-vedic-blue">{koota.score} / {koota.max}</div>
                    </div>
                ))}
            </div>

            <CosmicButton onClick={onReset} variant="secondary">Check Another Match</CosmicButton>
        </div>
    );
};

const initialState = {
    dob: '1995-01-01',
    tob: '12:00',
    location: '',
    lat: '',
    lon: '',
    year: '', month: '', day: '', hour: '', minute: '',
    tz: 'Asia/Kolkata'
};

const formatParams = (data) => {
    // Ensure lat/lon are present
    if (!data.lat || !data.lon) {
        throw new Error("Please enter and select a valid location for both profiles.");
    }
    const d = new Date(`${data.dob}T${data.tob}`);
    return {
        year: d.getFullYear(),
        month: d.getMonth() + 1,
        day: d.getDate(),
        hour: d.getHours(),
        minute: d.getMinutes(),
        second: 0,
        lat: parseFloat(data.lat),
        lon: parseFloat(data.lon),
        tz: 'Asia/Kolkata'
    };
};

export default MatchPage;
