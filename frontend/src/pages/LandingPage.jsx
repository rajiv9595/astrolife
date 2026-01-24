import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import Navbar from '../components/ui/Navbar';
import VedicButton from '../components/ui/VedicButton';
import VedicCard from '../components/ui/VedicCard';
import SignupForm from '../components/auth/SignupForm';
// We are hoisting the form directly onto the landing page as per reference img "Fill the form to get your kundli"
import { Star, Sun, Moon, ArrowRight, Heart, BookOpen, UserCheck, Compass, Sparkles } from 'lucide-react';

import { astroService } from '../services/astroService';
import ganeshaImage from '../assets/ganesha_circle.png';

const LandingPage = () => {
    const [panchang, setPanchang] = useState(null);

    useEffect(() => {
        const fetchPanchang = async () => {
            try {
                const now = new Date();
                const params = {
                    year: now.getFullYear(),
                    month: now.getMonth() + 1,
                    day: now.getDate(),
                    hour: now.getHours(),
                    minute: now.getMinutes(),
                    second: now.getSeconds(),
                    lat: 28.6139,
                    lon: 77.2090,
                    tz: "Asia/Kolkata",
                    planets: ["Sun", "Moon"] // Optimization
                };
                const data = await astroService.computeChart(params);
                setPanchang(data);
            } catch (err) {
                console.error("Failed to load Panchang", err);
            }
        };
        fetchPanchang();
    }, []);

    return (
        <div className="min-h-screen bg-vedic-cream font-sans">
            <Navbar />

            {/* Hero Section */}
            <section className="bg-vedic-blue relative overflow-hidden text-white pt-16 pb-24 px-6 md:px-12">
                {/* Background Decor */}
                <div className="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none bg-[url('https://www.transparenttextures.com/patterns/black-scales.png')]"></div>
                <div className="absolute -top-24 -right-24 w-96 h-96 rounded-full bg-vedic-orange blur-[150px] opacity-20"></div>

                <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center relative z-10">
                    {/* Text Content */}
                    <motion.div
                        initial={{ opacity: 0, x: -30 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.8 }}
                        className="text-center lg:text-left"
                    >
                        <h3 className="text-vedic-gold font-bold tracking-widest uppercase mb-4 text-sm">Welcome to LifePath</h3>
                        <h1 className="text-5xl md:text-6xl font-serif font-bold text-white mb-6 leading-tight">
                            Discover Your Cosmic <br className="hidden md:block" />
                            <span className="text-vedic-orange">Destiny Today</span>
                        </h1>
                        <div className="w-24 h-1 bg-vedic-orange mb-8 mx-auto lg:mx-0"></div>
                        <p className="text-lg text-stone-300 max-w-lg mb-8 leading-relaxed mx-auto lg:mx-0">
                            Expert Vedic Astrology consultation and precise Kundli generation using ancient wisdom and modern technology.
                        </p>
                        <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
                            <VedicButton variant="primary">Get Free Kundli</VedicButton>

                        </div>
                    </motion.div>

                    {/* Hero Image (Ganesha/Spiritual) */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.8, delay: 0.2 }}
                        className="flex justify-center"
                    >
                        {/* Placeholder until we have a real asset - using a styled decorative circle */}
                        <div className="w-[300px] h-[300px] md:w-[450px] md:h-[450px] border-[12px] border-white/10 rounded-full flex items-center justify-center relative">
                            <div className="absolute inset-0 border-[2px] border-vedic-orange/30 rounded-full animate-pulse-slow"></div>
                            <img
                                src={ganeshaImage}
                                alt="Lord Ganesha"
                                className="w-full h-full object-cover rounded-full"
                            />
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* Panchang / Daily Strip */}
            <section className="bg-white py-8 border-b border-stone-200 shadow-sm relative z-20 -mt-8 mx-6 md:mx-12 rounded-xl">
                <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-3 gap-8 text-center divide-y md:divide-y-0 md:divide-x divide-stone-100">
                    <PanchangItem
                        label="Tithi"
                        value={panchang?.tithi?.paksha || "Loading..."}
                        sub={panchang?.tithi?.name || "..."}
                    />
                    <PanchangItem
                        label="Nakshatra"
                        value={panchang?.nakshatra_of_moon?.nakshatra || "Loading..."}
                        sub={panchang?.nakshatra_of_moon?.lord ? `Lord: ${panchang.nakshatra_of_moon.lord}` : "..."}
                    />
                    <PanchangItem
                        label="Yoga"
                        value={panchang?.nithya_yoga?.name || "Loading..."}
                    />
                </div>
            </section>

            {/* Kundli Form Section - Directly mimicking user ref image */}
            <section className="py-24 px-6 bg-vedic-beige/30">
                <div className="max-w-6xl mx-auto">
                    <div className="text-center mb-16">
                        <h2 className="text-4xl font-serif font-bold text-vedic-blue mb-4">Generate Your Kundli</h2>
                        <div className="w-16 h-1 bg-vedic-orange mx-auto mb-4"></div>
                        <p className="text-vedic-muted max-w-2xl mx-auto">
                            Fill in your birth details to receive a comprehensive analysis of your life path, career, marriage, and health.
                        </p>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 bg-white rounded-2xl shadow-vedic overflow-hidden">
                        {/* Left: Illustration */}
                        <div className="bg-vedic-blue p-12 flex items-center justify-center relative overflow-hidden">
                            <div className="absolute inset-0 opacity-20 bg-[url('https://www.transparenttextures.com/patterns/stardust.png')]"></div>
                            <div className="relative z-10 text-center text-white">
                                <div className="text-9xl mb-6 opacity-80">💫</div>
                                <h3 className="text-2xl font-serif text-white mb-2">Detailed Analysis</h3>
                                <p className="text-stone-300 text-sm">Unlock the secrets of your stars</p>
                            </div>
                        </div>

                        {/* Right: The Form */}
                        <div className="p-8 md:p-12">
                            <h3 className="text-xl font-bold text-vedic-blue mb-6">Enter Birth Details</h3>
                            <SignupForm isEmbedded={true} isGuest={true} />
                            {/* Passing prop to adjust form style for landing page context */}
                        </div>
                    </div>
                </div>
            </section>

            {/* Services Grid */}
            <section className="py-24 px-6 bg-white">
                <div className="max-w-7xl mx-auto text-center">
                    <h2 className="text-4xl font-serif font-bold text-vedic-blue mb-4">Our Services</h2>
                    <p className="text-vedic-muted mb-16">Holistic guidance for every aspect of your life</p>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                        <ServiceCard title="Kundli Analysis" icon={Star} price="₹500" />
                        <ServiceCard title="AI Astrologer" icon={Sparkles} /> {/* New Feature */}
                        <ServiceCard title="Match Making" icon={Heart} price="₹300" />
                        <ServiceCard title="Career Consult" icon={Compass} price="₹800" />
                        <ServiceCard title="Gemstone Guide" icon={Sun} price="₹200" />
                        <ServiceCard title="Name Correction" icon={UserCheck} price="₹400" />
                        <ServiceCard title="Vastu Shastra" icon={BookOpen} price="₹1500" />
                        {/* Add more as needed */}
                    </div>

                    <div className="mt-16">
                        <VedicButton variant="primary" className="!px-12">View All Services</VedicButton>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="bg-vedic-cream border-t border-stone-200 pt-16 pb-8">
                <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-4 gap-12 mb-12">
                    <div className="col-span-1 md:col-span-1">
                        <div className="flex items-center gap-2 mb-6">
                            <div className="w-8 h-8 rounded-full bg-vedic-orange flex items-center justify-center text-white"><Sun size={20} /></div>
                            <span className="text-2xl font-serif font-bold text-vedic-blue">LifePath</span>
                        </div>
                        <p className="text-sm text-vedic-muted leading-relaxed">
                            Your trusted guide for Vedic Astrology services. Contact us for in-depth analysis and remedies.
                        </p>
                    </div>

                    <div>
                        <h4 className="text-lg font-bold text-vedic-blue mb-6">Useful Links</h4>
                        <ul className="space-y-3 text-sm text-vedic-muted">
                            <li><a href="/" className="hover:text-vedic-orange">Home</a></li>
                            <li><a href="/services" className="hover:text-vedic-orange">Services</a></li>
                            <li><a href="/about" className="hover:text-vedic-orange">About Us</a></li>
                            <li><a href="/about" className="hover:text-vedic-orange">Contact</a></li>
                        </ul>
                    </div>

                    <div>
                        <h4 className="text-lg font-bold text-vedic-blue mb-6">Contact</h4>
                        <ul className="space-y-3 text-sm text-vedic-muted">
                            <li>+91 98765 43210</li>
                            <li>info@lifepath.com</li>
                            <li>New Delhi, India</li>
                        </ul>
                    </div>

                    <div>
                        <h4 className="text-lg font-bold text-vedic-blue mb-6">Subscribe</h4>
                        <div className="flex flex-col gap-3">
                            <input className="w-full bg-white border border-stone-200 rounded px-4 py-3 text-sm" placeholder="Your Email" />
                            <VedicButton variant="primary" className="w-full">Subscribe</VedicButton>
                        </div>
                    </div>
                </div>
                <div className="text-center text-xs text-stone-400 border-t border-stone-200 pt-8">
                    © 2024 LifePath Vedic Astrology. All Rights Reserved.
                </div>
            </footer>
        </div>
    );
};

const PanchangItem = ({ label, value, sub, color }) => (
    <div className="flex flex-col gap-1">
        <span className="text-xs uppercase tracking-widest text-stone-400">{label}</span>
        <span className={`text-lg font-bold text-vedic-blue ${color}`}>{value}</span>
        {sub && <span className="text-xs text-stone-500">{sub}</span>}
    </div>
);

const ServiceCard = ({ icon: Icon, title }) => (
    <VedicCard hoverEffect className="p-8 text-center flex flex-col items-center">
        <div className="w-16 h-16 rounded-full bg-vedic-beige flex items-center justify-center text-vedic-orange mb-6">
            <Icon size={32} />
        </div>
        <h3 className="text-lg font-bold text-vedic-blue mb-2">{title}</h3>
        {/* Price removed as per request */}
        <a href="#" className="text-xs font-bold text-vedic-orange uppercase tracking-wide hover:underline">Read More</a>
    </VedicCard>
);

export default LandingPage;
