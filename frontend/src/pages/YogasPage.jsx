import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/ui/Navbar';
import VedicCard from '../components/ui/VedicCard';
import { authService } from '../services/authService';
import { astroService } from '../services/astroService';
import { ArrowLeft, Star, X, Info } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-toastify';

// Static mapping for rich details (since backend provides minimal info)
const YOGA_DETAILS = {
    "dhana_yoga_basic": {
        title: "Dhana Yoga",
        formation: "Formed when the 2nd Lord (Wealth) and 11th Lord (Gains) connect, or when the 2nd Lord and 9th Lord (Fortune) form a relationship.",
        benefits: "Signifies great wealth, financial stability, and the ability to accumulate assets. The native is likely to have multiple sources of income and enjoy material prosperity.",
        timing: "Results are most prominent during the Dasha or Antardasha of the 2nd, 9th, or 11th lords, or the planets forming the yoga."
    },
    "yogakaraka_basic": {
        title: "Raja Yoga (Yogakaraka)",
        formation: "Formed when a single planet rules both a Kendra (1, 4, 7, 10) and a Trikona (1, 5, 9) house.",
        benefits: "This is a powerful yoga for power, status, and success. It grants the native authority, fame, and the ability to rise high in their career or public life.",
        timing: "Activation occurs during the Mahadasha or Antardasha of the Yogakaraka planet."
    },
    "viparita_rajayoga_basic": {
        title: "Viparita Raja Yoga",
        formation: "Formed when lords of Dusthana houses (6, 8, 12) occupy other Dusthana houses (e.g., 6th lord in 8th).",
        benefits: "Success comes after struggle or through the misfortune of others. It gives the ability to overcome enemies, sudden gains, and resilience in difficult times.",
        timing: "Triggers during the periods of the planets involved, often bringing sudden turnarounds in difficult situations."
    },
    "harsha_yoga": {
        title: "Harsha Yoga",
        formation: "Formed when the 6th Lord is placed in the 6th, 8th, or 12th house.",
        benefits: "Makes the native invincible against enemies. They are healthy, fortunate, renowned, and enjoy happiness despite obstacles.",
        timing: "Operates during the dasha of the 6th Lord."
    },
    "sarala_yoga": {
        title: "Sarala Yoga",
        formation: "Formed when the 8th Lord is placed in the 6th, 8th, or 12th house.",
        benefits: "Confers long life, fearlessness, prosperity, and the ability to triumph over difficulties. The native is learned and respected.",
        timing: "Operates during the dasha of the 8th Lord."
    },
    "vimala_yoga": {
        title: "Vimala Yoga",
        formation: "Formed when the 12th Lord is placed in the 6th, 8th, or 12th house.",
        benefits: "Makes the native frugal, happy, and independent. They accumulate wealth and are known for their good qualities and spiritual inclination.",
        timing: "Operates during the dasha of the 12th Lord."
    },
    "gaja_kesari_yoga": {
        title: "Gaja Kesari Yoga",
        formation: "Jupiter is in a Kendra (1, 4, 7, 10) from the Moon.",
        benefits: "One of the most auspicious yogas. It gives fame, longevity, intelligence, and virtuous children. The native is capable of overpowering enemies like a lion (Kesari) overpowers an elephant (Gaja).",
        timing: "Strongest during Jupiter-Moon or Moon-Jupiter periods."
    },
    "budhaditya_yoga": {
        title: "Budhaditya Yoga",
        formation: "Conjunction of Sun and Mercury in a house.",
        benefits: "Grants high intelligence, skill in communication, and academic success. It is common but effective for professions involving intellect.",
        timing: "Active during Sun-Mercury periods."
    },
    "pancha_mahapurusha_hamsa": {
        title: "Hamsa Yoga",
        formation: "Jupiter is exalted or in its own sign in a Kendra house.",
        benefits: "Makes the native wise, spiritual, and respected. They may have marks of a lotus on their feet and live a righteous life.",
        timing: "During Jupiter dasha."
    },
    "pancha_mahapurusha_malavya": {
        title: "Malavya Yoga",
        formation: "Venus is exalted or in its own sign in a Kendra house.",
        benefits: "Gives a life of luxury, beauty, and artistic talent. The native enjoys good vehicles, refined tastes, and marital happiness.",
        timing: "During Venus dasha."
    }
};

const YogasPage = () => {
    const navigate = useNavigate();
    const [yogas, setYogas] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedYoga, setSelectedYoga] = useState(null);

    useEffect(() => {
        const fetchYogas = async () => {
            try {
                // Always fetch fresh data to ensure we have the latest Yogas from backend
                const formData = await authService.getChartDataParams();
                if (!formData) {
                    toast.error("Please enter birth details.");
                    navigate('/enter-details');
                    return;
                }
                const data = await astroService.computeChart(formData);
                setYogas(data.yogas || []);
                // Update cache with fresh data
                localStorage.setItem('chartData', JSON.stringify(data));
                setLoading(false);

            } catch (err) {
                console.error("Error loading yogas:", err);
                toast.error("Could not load yogas.");
                setLoading(false);
            }
        };

        fetchYogas();
    }, [navigate]);

    const getYogaContent = (yoga) => {
        const staticDetails = YOGA_DETAILS[yoga.id] || YOGA_DETAILS[yoga.name]; // Fallback to ID key or Name key

        return {
            title: staticDetails?.title || yoga.name,
            formation: staticDetails?.formation || yoga.description || "Specific planetary combination based on Vedic rules.",
            benefits: staticDetails?.benefits || "This combination is considered impactful for the native's life path.",
            timing: staticDetails?.timing || "Results vary based on the strength of the planets involved and their dasha periods."
        };
    };

    return (
        <div className="font-sans min-h-screen bg-vedic-cream relative">

            <main className="max-w-6xl mx-auto px-4 py-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-serif font-bold text-vedic-blue">Important Yogas</h1>
                    <p className="text-stone-600 mt-2">
                        Special planetary combinations present in your birth chart.
                    </p>
                </div>

                {loading ? (
                    <div className="flex justify-center py-20">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-vedic-orange"></div>
                    </div>
                ) : yogas.filter(y => y.status === 'STRONG' || y.status === 'ACTIVE').length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {yogas.filter(y => y.status === 'STRONG' || y.status === 'ACTIVE').map((yoga, idx) => {
                            const content = getYogaContent(yoga);
                            return (
                                <motion.div
                                    key={idx}
                                    whileHover={{ y: -5 }}
                                    onClick={() => setSelectedYoga(yoga)}
                                    className="cursor-pointer"
                                >
                                    <VedicCard className="h-full bg-white hover:shadow-lg transition-shadow border border-transparent hover:border-vedic-orange/30 p-6 flex flex-col items-center text-center">
                                        <div className="w-12 h-12 rounded-full bg-vedic-orange/10 flex items-center justify-center text-vedic-orange mb-4">
                                            <Star size={24} fill="currentColor" />
                                        </div>
                                        <h3 className="text-lg font-bold text-vedic-blue mb-2 font-serif">{content.title}</h3>
                                        <p className="text-sm text-stone-500 line-clamp-3">
                                            {content.formation}
                                        </p>
                                        <div className="mt-4 text-xs font-bold text-vedic-orange uppercase tracking-wider">
                                            Read More
                                        </div>
                                    </VedicCard>
                                </motion.div>
                            );
                        })}
                    </div>
                ) : (
                    <div className="text-center py-20 bg-white rounded-xl shadow-sm">
                        <p className="text-stone-500">No major public yogas detected in this basic scan.</p>
                    </div>
                )}
            </main>

            {/* Modal for Details */}
            <AnimatePresence>
                {selectedYoga && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
                        onClick={() => setSelectedYoga(null)}>
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            onClick={(e) => e.stopPropagation()}
                            className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden relative"
                        >
                            <button
                                onClick={() => setSelectedYoga(null)}
                                className="absolute top-4 right-4 p-2 bg-stone-100 rounded-full hover:bg-stone-200 transition-colors"
                            >
                                <X size={20} className="text-stone-600" />
                            </button>

                            {/* Modal Header */}
                            <div className="bg-vedic-blue p-8 text-white">
                                <div className="flex items-center gap-3 mb-2 opacity-80">
                                    <Star size={18} />
                                    <span className="text-sm font-bold uppercase tracking-wider">Yoga Details</span>
                                </div>
                                <h2 className="text-3xl font-serif font-bold">
                                    {getYogaContent(selectedYoga).title}
                                </h2>
                            </div>

                            {/* Modal Content */}
                            <div className="p-8 space-y-6 max-h-[70vh] overflow-y-auto custom-scrollbar">

                                <div className="bg-vedic-orange/5 p-6 rounded-xl border border-vedic-orange/10">
                                    <h4 className="flex items-center gap-2 font-bold text-vedic-blue mb-2">
                                        <Info size={18} className="text-vedic-orange" />
                                        How it Forms
                                    </h4>
                                    <p className="text-stone-700 leading-relaxed">
                                        {getYogaContent(selectedYoga).formation}
                                    </p>
                                </div>

                                <div>
                                    <h4 className="font-bold text-lg text-vedic-blue mb-3">Benefits & Effects</h4>
                                    <p className="text-stone-600 leading-relaxed text-sm md:text-base">
                                        {getYogaContent(selectedYoga).benefits}
                                    </p>
                                </div>

                                <div>
                                    <h4 className="font-bold text-lg text-vedic-blue mb-3">When will it manifest?</h4>
                                    <div className="flex items-start gap-4 bg-stone-50 p-4 rounded-lg">
                                        <div className="mt-1 bg-white p-2 rounded shadow-sm">
                                            <ClockIcon />
                                        </div>
                                        <div>
                                            <p className="text-stone-600 text-sm leading-relaxed">
                                                {getYogaContent(selectedYoga).timing}
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                {selectedYoga.score && (
                                    <div className="pt-4 border-t border-stone-100 flex justify-between items-center text-xs text-stone-400">
                                        <span>Strength Score: {selectedYoga.score}%</span>
                                        <span>Status: {selectedYoga.status}</span>
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    );
};

// Simple Icon Component
const ClockIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-vedic-orange">
        <circle cx="12" cy="12" r="10"></circle>
        <polyline points="12 6 12 12 16 14"></polyline>
    </svg>
);

export default YogasPage;
