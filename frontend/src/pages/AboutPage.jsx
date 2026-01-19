import React from 'react';
import Navbar from '../components/ui/Navbar';
import { motion } from 'framer-motion';
import { Mail, Phone, MapPin, Globe, Linkedin, Github } from 'lucide-react';

const AboutPage = () => {
    return (
        <div className="min-h-screen bg-vedic-cream font-sans">
            <Navbar />

            {/* Hero Section */}
            <section className="bg-vedic-blue text-white py-20 px-6 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-96 h-96 bg-vedic-orange opacity-10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
                <div className="max-w-4xl mx-auto text-center relative z-10">
                    <motion.h1
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="text-4xl md:text-6xl font-serif font-bold mb-6"
                    >
                        Bridging Ancient Wisdom <br /> <span className="text-vedic-orange">& Modern Tech</span>
                    </motion.h1>
                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="text-lg md:text-xl text-stone-300 leading-relaxed"
                    >
                        Our mission is to decode the cosmic language of the stars and translate it into clear, actionable guidance for your life's journey.
                    </motion.p>
                </div>
            </section>

            {/* Our Story / Intent */}
            <section className="py-20 px-6 bg-white">
                <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-16 items-center">
                    <div>
                        <div className="w-16 h-1 bg-vedic-orange mb-6"></div>
                        <h2 className="text-3xl font-serif font-bold text-vedic-blue mb-6">Our Philosophy</h2>
                        <div className="space-y-4 text-stone-600 leading-relaxed">
                            <p>
                                Vedic Astrology, or Jyotish Shastra, is the "Science of Light." For millennia, it has served as a guiding lamp for humanity, helping us understand our karma, our purpose, and our timing.
                            </p>
                            <p>
                                However, in the modern digital age, this profound wisdom is often diluted or made inaccessible by complex jargon. <strong>LifePath</strong> was born out of a desire to change that.
                            </p>
                            <p>
                                We believe that astrology is not about fatalism; it is about empowerment. By combining precise astronomical calculations with intuitive, user-friendly design, we aim to bring the authentic depths of Vedic astrology to your fingertips. Whether you are seeking clarity in your career, harmony in relationships, or just a better understanding of yourself, we are here to help you navigate your path.
                            </p>
                        </div>
                    </div>
                    <div className="relative">
                        <div className="absolute inset-0 bg-vedic-orange/5 rounded-2xl transform rotate-3"></div>
                        <img
                            src="https://images.unsplash.com/photo-1532012197267-da84d127e765?q=80&w=2574&auto=format&fit=crop"
                            alt="Cosmic Compass"
                            className="relative rounded-2xl shadow-xl border-4 border-white"
                        />
                    </div>
                </div>
            </section>

            {/* Founder Section */}
            <section className="py-20 px-6 bg-vedic-beige/30">
                <div className="max-w-4xl mx-auto">
                    <div className="text-center mb-12">
                        <h2 className="text-3xl font-serif font-bold text-vedic-blue mb-4">Meet the Creator</h2>
                        <p className="text-vedic-muted">The mind behind the code and the cosmos</p>
                    </div>

                    <div className="bg-white rounded-2xl shadow-vedic overflow-hidden md:flex">
                        <div className="md:w-2/5 bg-vedic-blue relative min-h-[300px]">
                            {/* Placeholder for Profile Image */}
                            <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-vedic-blue to-black">
                                <span className="text-8xl">👨‍💻</span>
                            </div>
                        </div>
                        <div className="md:w-3/5 p-8 md:p-12 flex flex-col justify-center">
                            <h3 className="text-2xl font-bold text-vedic-blue">M. Rajeev Reddy</h3>
                            <p className="text-vedic-orange font-bold text-sm uppercase tracking-wider mb-4">B.Tech | Founder & Lead Developer</p>

                            <p className="text-stone-600 mb-8 leading-relaxed">
                                With a strong technical foundation and a passionate curiosity for the mystic arts, Rajeev built LifePath to be a sanctuary of clarity. He is dedicated to building tools that respect the tradition of the sages while embracing the speed and precision of modern computing.
                            </p>

                            <div className="space-y-3">
                                <div className="flex items-center gap-3 text-stone-600">
                                    <div className="w-8 h-8 rounded-full bg-vedic-orange/10 flex items-center justify-center text-vedic-orange">
                                        <Phone size={16} />
                                    </div>
                                    <span className="font-medium">+91 96143 46666</span>
                                </div>
                                <div className="flex items-center gap-3 text-stone-600">
                                    <div className="w-8 h-8 rounded-full bg-vedic-orange/10 flex items-center justify-center text-vedic-orange">
                                        <Mail size={16} />
                                    </div>
                                    <span className="font-medium">medapatirajiv9494@gmail.com</span>
                                </div>
                                <div className="flex items-center gap-3 text-stone-600">
                                    <div className="w-8 h-8 rounded-full bg-vedic-orange/10 flex items-center justify-center text-vedic-orange">
                                        <MapPin size={16} />
                                    </div>
                                    <span className="font-medium">India</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer CTA */}
            <section className="py-20 px-6 bg-vedic-blue text-white text-center">
                <h2 className="text-3xl font-serif font-bold mb-6">Start Your Journey Today</h2>
                <p className="text-stone-300 max-w-xl mx-auto mb-8">
                    Discover what the stars have in store for you with our accurate and detailed reports.
                </p>
                <button
                    onClick={() => window.location.href = '/enter-details'}
                    className="bg-vedic-orange hover:bg-orange-600 text-white px-8 py-3 rounded-lg font-bold transition-transform hover:scale-105"
                >
                    Get Your Free Kundli
                </button>
            </section>
        </div>
    );
};

export default AboutPage;
