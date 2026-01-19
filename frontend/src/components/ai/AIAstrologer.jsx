import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { aiService } from '../../services/aiService';
import CosmicButton from '../ui/CosmicButton';
import { Send, MessageSquare, X, Sparkles } from 'lucide-react';
import classNames from 'classnames';

const AIAstrologer = ({ chartData }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [query, setQuery] = useState('');
    const [messages, setMessages] = useState([
        { role: 'assistant', text: 'Hari Om! I have analyzed your birth chart. What would you like to know regarding your destiny?' }
    ]);
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [messages]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!query.trim()) return;

        const userMsg = { role: 'user', text: query };
        setMessages(prev => [...prev, userMsg]);
        setQuery('');
        setLoading(true);

        try {
            const result = await aiService.analyze(query, chartData);
            setMessages(prev => [...prev, { role: 'assistant', text: result.response }]);
        } catch (err) {
            setMessages(prev => [...prev, { role: 'assistant', text: "The cosmic signals are weak right now. Please try again." }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            {/* Floating Toggle Button */}
            <motion.button
                className="fixed bottom-6 right-6 z-50 p-4 rounded-full bg-nebula-purple text-white shadow-lg shadow-purple-500/40 hover:scale-110 transition-transform"
                onClick={() => setIsOpen(true)}
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                whileHover={{ rotate: 15 }}
            >
                <Sparkles size={24} />
            </motion.button>

            {/* Chat Interface */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: 100, scale: 0.9 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 100, scale: 0.9 }}
                        className="fixed bottom-24 right-6 z-50 w-96 h-[600px] max-h-[80vh] flex flex-col bg-cosmic-dark/95 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl overflow-hidden"
                    >
                        {/* Header */}
                        <div className="p-4 bg-gradient-to-r from-nebula-purple to-purple-800 flex items-center justify-between shadow-lg">
                            <div className="flex items-center gap-2 text-white">
                                <Sparkles size={18} />
                                <span className="font-serif font-bold">AI Vedic Astrologer</span>
                            </div>
                            <button onClick={() => setIsOpen(false)} className="text-white/80 hover:text-white">
                                <X size={20} />
                            </button>
                        </div>

                        {/* Messages */}
                        <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
                            {messages.map((msg, idx) => (
                                <div
                                    key={idx}
                                    className={classNames(
                                        "max-w-[85%] p-3 rounded-xl text-sm leading-relaxed",
                                        msg.role === 'user'
                                            ? "ml-auto bg-white/10 text-white rounded-br-none"
                                            : "mr-auto bg-purple-900/30 text-gray-200 rounded-bl-none border border-purple-500/20"
                                    )}
                                >
                                    {msg.text}
                                </div>
                            ))}
                            {loading && (
                                <div className="mr-auto bg-purple-900/30 p-3 rounded-xl rounded-bl-none border border-purple-500/20 flex gap-1">
                                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" />
                                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce delay-100" />
                                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce delay-200" />
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                        {/* Input */}
                        <form onSubmit={handleSend} className="p-4 border-t border-white/10 bg-white/5">
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    value={query}
                                    onChange={e => setQuery(e.target.value)}
                                    placeholder="Ask about your career, marriage..."
                                    className="flex-1 bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-purple-500"
                                />
                                <button
                                    type="submit"
                                    disabled={loading || !query.trim()}
                                    className="p-2 bg-nebula-purple rounded-lg text-white hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                >
                                    <Send size={18} />
                                </button>
                            </div>
                        </form>
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
};

export default AIAstrologer;
