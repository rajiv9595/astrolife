import React, { useState } from 'react';
import Navbar from '../components/ui/Navbar';
import VedicCard from '../components/ui/VedicCard';
import { Calendar, User, ArrowRight, Tag, BookOpen, Clock } from 'lucide-react';
import { motion } from 'framer-motion';

// Sample Mock Data
const BLOG_POSTS = [
    {
        id: 1,
        title: "Understanding Saturn's Sade Sati: It's Not All Bad",
        excerpt: "The 7.5 year cycle of Saturn is often feared, but it is actually a period of immense growth, restructuring, and karmic balancing. Learn how to navigate it.",
        category: "Planetary Transits",
        author: "Pandit Sharma",
        date: "Oct 12, 2024",
        readTime: "5 min read",
        image: "https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=2694&auto=format&fit=crop"
    },
    {
        id: 2,
        title: "The 5 Mahapurusha Yogas: Are You Born for Greatness?",
        excerpt: "Pancha Mahapurusha Yogas are formed by Mars, Mercury, Jupiter, Venus, and Saturn. Discover if your chart holds the promise of a legendary life.",
        category: "Vedic Yogas",
        author: "Dr. A. Rao",
        date: "Oct 08, 2024",
        readTime: "8 min read",
        image: "https://images.unsplash.com/photo-1506318137071-a8bcbf6755dd?q=80&w=2670&auto=format&fit=crop"
    },
    {
        id: 3,
        title: "Retrograde Planets: Karmic Lessons from Past Lives",
        excerpt: "When a planet appears to move backward, its energy turns inward. Retrograde planets in your birth chart indicate unfinished business from previous incarnations.",
        category: "Karma & Reincarnation",
        author: "Priya Singh",
        date: "Sep 25, 2024",
        readTime: "6 min read",
        image: "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?q=80&w=2022&auto=format&fit=crop"
    },
    {
        id: 4,
        title: "Choosing the Right Gemstone: Myths vs Reality",
        excerpt: "Gemstones can amplify planetary energy, but wearing the wrong one can be disastrous. Why you should never wear a Blue Sapphire without a trial.",
        category: "Remedies",
        author: "Pandit Sharma",
        date: "Sep 15, 2024",
        readTime: "4 min read",
        image: "https://images.unsplash.com/photo-1615486511484-92e172cc416d?q=80&w=2670&auto=format&fit=crop"
    }
];

const BlogPage = () => {
    const [selectedCategory, setSelectedCategory] = useState("All");

    const filteredPosts = selectedCategory === "All"
        ? BLOG_POSTS
        : BLOG_POSTS.filter(post => post.category === selectedCategory);

    return (
        <div className="min-h-screen bg-vedic-cream">
            <Navbar />

            {/* Hero Section */}
            <div className="bg-vedic-blue text-white py-20 px-6 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-96 h-96 bg-vedic-orange opacity-10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
                <div className="max-w-7xl mx-auto relative z-10 text-center">
                    <motion.h1
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-4xl md:text-5xl font-serif font-bold mb-6"
                    >
                        Vedic Wisdom & Insights
                    </motion.h1>
                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="text-xl text-stone-300 max-w-2xl mx-auto"
                    >
                        Explore the ancient secrets of the stars, decode planetary movements, and learn how to align your life with cosmic rhythms.
                    </motion.p>
                </div>
            </div>

            {/* Content Area */}
            <div className="max-w-7xl mx-auto px-6 py-12 grid grid-cols-1 lg:grid-cols-4 gap-12">

                {/* Main Feed */}
                <div className="lg:col-span-3 space-y-10">
                    <div className="flex items-center justify-between border-b border-stone-200 pb-4">
                        <h2 className="text-2xl font-bold text-vedic-blue text-serif">Latest Articles</h2>
                        <span className="text-sm text-stone-500">Showing {filteredPosts.length} posts</span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {filteredPosts.map((post) => (
                            <motion.div
                                key={post.id}
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                whileHover={{ y: -5 }}
                                className="bg-white rounded-xl overflow-hidden shadow-vedic hover:shadow-xl transition-all cursor-pointer group"
                            >
                                <div className="h-48 overflow-hidden">
                                    <img
                                        src={post.image}
                                        alt={post.title}
                                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
                                    />
                                </div>
                                <div className="p-6">
                                    <div className="flex gap-2 mb-3">
                                        <span className="text-[10px] font-bold uppercase tracking-wider text-vedic-orange bg-vedic-orange/10 px-2 py-1 rounded">
                                            {post.category}
                                        </span>
                                    </div>
                                    <h3 className="text-xl font-bold text-vedic-blue mb-3 group-hover:text-vedic-orange transition-colors line-clamp-2">
                                        {post.title}
                                    </h3>
                                    <p className="text-stone-600 text-sm mb-4 line-clamp-3">
                                        {post.excerpt}
                                    </p>
                                    <div className="flex items-center justify-between text-xs text-stone-400 border-t border-stone-100 pt-4">
                                        <div className="flex items-center gap-4">
                                            <span className="flex items-center gap-1"><User size={12} /> {post.author}</span>
                                            <span className="flex items-center gap-1"><Calendar size={12} /> {post.date}</span>
                                        </div>
                                        <span className="flex items-center gap-1 text-vedic-blue font-medium"><Clock size={12} /> {post.readTime}</span>
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </div>

                {/* Sidebar */}
                <div className="lg:col-span-1 space-y-8">
                    {/* Categories Widget */}
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-stone-100">
                        <h3 className="font-bold text-lg text-vedic-blue mb-4 flex items-center gap-2">
                            <Tag size={18} /> Categories
                        </h3>
                        <div className="space-y-2">
                            {['All', 'Planetary Transits', 'Vedic Yogas', 'Karma & Reincarnation', 'Remedies', 'Spirituality'].map(cat => (
                                <button
                                    key={cat}
                                    onClick={() => setSelectedCategory(cat)}
                                    className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${selectedCategory === cat ? 'bg-vedic-orange text-white' : 'text-stone-600 hover:bg-stone-50'}`}
                                >
                                    {cat}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Newsletter Widget */}
                    <div className="bg-vedic-blue p-6 rounded-xl text-white">
                        <h3 className="font-bold text-lg mb-2">Weekly Horoscope</h3>
                        <p className="text-sm text-stone-300 mb-4">Get personalized predictions delivered to your inbox every Monday.</p>
                        <input
                            type="email"
                            placeholder="Your email address"
                            className="w-full px-3 py-2 rounded text-stone-900 text-sm mb-2 focus:outline-none"
                        />
                        <button className="w-full bg-vedic-orange py-2 rounded text-sm font-bold hover:bg-orange-600 transition-colors">
                            Subscribe
                        </button>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default BlogPage;
