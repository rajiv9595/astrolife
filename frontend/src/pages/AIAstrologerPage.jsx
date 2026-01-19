import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { aiService } from '../services/aiService';
import { authService } from '../services/authService';
import { astroService } from '../services/astroService';
import { Send, Bot, Sparkles, User as UserIcon } from 'lucide-react';
import classNames from 'classnames';
import ReactMarkdown from 'react-markdown';

const AIAstrologerPage = () => {
    const [query, setQuery] = useState('');
    const [chartData, setChartData] = useState(null);
    const [messages, setMessages] = useState([
        { role: 'assistant', text: 'Hari Om! I am your AI Vedic Astrologer. I have analyzed your birth chart to provide personalized insights.\n\nAsk me anything about your:\n- Career path and success\n- Marriage and relationships\n- Wealth and financial prospects\n- Health and well-being' }
    ]);
    const [loading, setLoading] = useState(false);
    const [initializing, setInitializing] = useState(true);
    const messagesEndRef = useRef(null);

    useEffect(() => {
        const init = async () => {
            try {
                // Fetch chart data so the AI has context
                const params = await authService.getChartDataParams();
                const data = await astroService.computeChart(params);
                setChartData(data);
            } catch (err) {
                console.error("Failed to load chart context", err);
                setMessages(prev => [...prev, { role: 'assistant', text: "_Note: I am having trouble accessing your chart details directly. I will do my best to answer based on general principles._" }]);
            } finally {
                setInitializing(false);
            }
        };
        init();
    }, []);

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

    if (initializing) {
        return (
            <div className="flex flex-col items-center justify-center h-96 gap-4">
                <div className="w-12 h-12 border-4 border-vedic-orange border-t-transparent rounded-full animate-spin" />
                <p className="text-vedic-blue font-bold animate-pulse">Aligning with the Stars...</p>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-[calc(100vh-140px)] bg-white rounded-xl shadow-sm border border-stone-200 overflow-hidden">
            {/* Header */}
            <div className="bg-vedic-blue p-4 border-b border-white/10 flex items-center gap-3 text-white shadow-md z-10">
                <div className="w-10 h-10 rounded-full bg-vedic-orange/20 flex items-center justify-center border border-vedic-orange">
                    <Bot size={24} className="text-vedic-orange" />
                </div>
                <div>
                    <h1 className="text-lg font-serif font-bold">AI Vedic Astrologer</h1>
                    <p className="text-xs text-stone-300 flex items-center gap-1">
                        <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                        Online & Ready to Guide
                    </p>
                </div>
            </div>

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 bg-stone-50/50 custom-scrollbar">
                {messages.map((msg, idx) => (
                    <motion.div
                        key={idx}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={classNames(
                            "flex gap-4 max-w-4xl mx-auto",
                            msg.role === 'user' ? "flex-row-reverse" : "flex-row"
                        )}
                    >
                        {/* Avatar */}
                        <div className={classNames(
                            "w-8 h-8 rounded-full flex items-center justify-center shrink-0 border mt-1",
                            msg.role === 'user'
                                ? "bg-stone-200 border-stone-300 text-stone-600"
                                : "bg-vedic-orange/10 border-vedic-orange/30 text-vedic-orange"
                        )}>
                            {msg.role === 'user' ? <UserIcon size={16} /> : <Sparkles size={16} />}
                        </div>

                        {/* Bubble */}
                        <div className={classNames(
                            "group relative p-4 rounded-2xl text-sm md:text-base leading-relaxed shadow-sm max-w-[80%]",
                            msg.role === 'user'
                                ? "bg-vedic-blue text-white rounded-tr-none"
                                : "bg-white text-stone-700 border border-stone-200 rounded-tl-none"
                        )}>
                            <div className="prose prose-sm max-w-none dark:prose-invert">
                                <ReactMarkdown>{msg.text}</ReactMarkdown>
                            </div>
                        </div>
                    </motion.div>
                ))}

                {loading && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex gap-4 max-w-4xl mx-auto"
                    >
                        <div className="w-8 h-8 rounded-full bg-vedic-orange/10 border border-vedic-orange/30 flex items-center justify-center shrink-0 mt-1">
                            <Sparkles size={16} className="text-vedic-orange animate-spin-slow" />
                        </div>
                        <div className="bg-white border border-stone-200 p-4 rounded-2xl rounded-tl-none flex gap-1 items-center shadow-sm">
                            <div className="w-2 h-2 bg-vedic-orange rounded-full animate-bounce" />
                            <div className="w-2 h-2 bg-vedic-orange rounded-full animate-bounce delay-100" />
                            <div className="w-2 h-2 bg-vedic-orange rounded-full animate-bounce delay-200" />
                        </div>
                    </motion.div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 bg-white border-t border-stone-200">
                <form onSubmit={handleSend} className="max-w-4xl mx-auto relative flex gap-3">
                    <input
                        type="text"
                        value={query}
                        onChange={e => setQuery(e.target.value)}
                        placeholder="Ask a question about your chart..."
                        className="flex-1 bg-stone-50 border border-stone-200 rounded-xl px-4 py-3 text-stone-700 
                                 focus:outline-none focus:ring-2 focus:ring-vedic-orange/20 focus:border-vedic-orange transition-all"
                    />
                    <button
                        type="submit"
                        disabled={loading || !query.trim()}
                        className="px-6 py-3 bg-vedic-orange hover:bg-orange-600 text-white rounded-xl font-bold shadow-md 
                                 hover:shadow-lg disabled:opacity-50 disabled:shadow-none transition-all flex items-center gap-2"
                    >
                        <span>Send</span>
                        <Send size={18} />
                    </button>
                </form>
                <div className="text-center mt-2">
                    <p className="text-[10px] text-stone-400">
                        AI can make mistakes. Please verify important astrological details with a professional.
                    </p>
                </div>
            </div>
        </div>
    );
};

export default AIAstrologerPage;
