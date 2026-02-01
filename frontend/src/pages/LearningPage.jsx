import React, { useState, useEffect, useRef } from 'react';
import Navbar from '../components/ui/Navbar';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, Sparkles, Send, ArrowLeft, RefreshCw, X, History } from 'lucide-react';
import api from '../services/api';
import ReactMarkdown from 'react-markdown';
import { toast } from 'react-toastify';

const BOOKS = [
    {
        id: 'prasna',
        title: 'Prasna Marga',
        author: 'Harihara', // (Nilakantha) - 1649 CE
        sub: '(Nilakantha) - 1649 CE',
        description: 'Vedic horary astrology & chart interpretation',
        cover: '/books/prasna_marga.png',
        color: 'from-orange-50 to-red-50',
        text_color: 'text-red-800'
    },
    {
        id: 'bphs',
        title: 'Bṛhat Parāśara Horā Śāstra',
        author: 'Maharishi Parashara', // 3102 BC
        sub: '- 3000 BC',
        description: 'Main text of Vedic astrology system',
        cover: '/books/bphs.png',
        color: 'from-slate-50 to-stone-100',
        text_color: 'text-slate-800'
    },
    {
        id: 'saravali',
        title: 'Saravali',
        author: 'Kalyanavarma',
        sub: '- 800 CE',
        description: 'Essential charts and planetary combinations',
        cover: '/books/saravali.png',
        color: 'from-purple-50 to-indigo-50',
        text_color: 'text-purple-800'
    }
];

const LearningPage = () => {
    const [selectedBook, setSelectedBook] = useState(null);

    return (
        <div className="min-h-screen bg-vedic-cream flex flex-col">
            <Navbar />

            <div className="flex-1 max-w-7xl mx-auto w-full pt-8 px-4 sm:px-6 pb-20">
                <AnimatePresence mode="wait">
                    {!selectedBook ? (
                        <motion.div
                            key="library"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            className="space-y-8"
                        >
                            <div className="text-center space-y-4 mb-12">
                                <span className="inline-block px-3 py-1 bg-vedic-orange/10 text-vedic-orange rounded-full text-xs font-bold uppercase tracking-wider">
                                    AI Guru Teacher
                                </span>
                                <h1 className="text-4xl md:text-5xl font-serif font-bold text-vedic-blue">
                                    Learn from the <span className="text-transparent bg-clip-text bg-gradient-to-r from-vedic-orange to-vedic-gold">Classics</span>
                                </h1>
                                <p className="text-stone-600 max-w-2xl mx-auto">
                                    Select a sacred text below to start a conversation with your AI Guru trained specifically on that book's philosophy.
                                </p>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                                {BOOKS.map((book) => (
                                    <motion.div
                                        whileHover={{ y: -5 }}
                                        key={book.id}
                                        onClick={() => setSelectedBook(book)}
                                        className="bg-white rounded-2xl p-4 shadow-lg hover:shadow-xl transition-all cursor-pointer group border border-stone-100"
                                    >
                                        <div className={`aspect-[3/4] rounded-xl overflow-hidden bg-gradient-to-br ${book.color} mb-6 relative`}>
                                            <img
                                                src={book.cover}
                                                alt={book.title}
                                                className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                                            />
                                            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
                                                <div className="bg-white/90 backdrop-blur text-vedic-blue px-6 py-2 rounded-full font-bold text-sm transform translate-y-4 group-hover:translate-y-0 transition-transform">
                                                    Start Learning
                                                </div>
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <h3 className="font-serif font-bold text-xl text-vedic-blue leading-tight group-hover:text-vedic-orange transition-colors">
                                                {book.title}
                                            </h3>
                                            <div className="flex justify-between items-center text-xs text-stone-500 font-medium uppercase tracking-wide">
                                                <span>{book.author}</span>
                                                <span>{book.sub}</span>
                                            </div>
                                            <p className="text-sm text-stone-600 line-clamp-2 pt-2">
                                                {book.description}
                                            </p>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        </motion.div>
                    ) : (
                        <GuruChatInterface book={selectedBook} onBack={() => setSelectedBook(null)} />
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};

const GuruChatInterface = ({ book, onBack }) => {
    const [messages, setMessages] = useState([
        {
            role: 'assistant',
            content: `Namaste. I am your specialized teacher for **${book.title}**. Ask me any question related to this text, and I will explain it using the wisdom of ${book.author}.`
        }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const scrollRef = useRef(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMsg = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const res = await api.post('/learn/guru-chat', {
                message: userMsg.content,
                book_title: book.title,
                book_author: book.author
            });

            setMessages(prev => [...prev, { role: 'assistant', content: res.data.reply }]);
        } catch (err) {
            setMessages(prev => [...prev, { role: 'assistant', content: 'The stars are cloudy right now. Please try again in a moment.' }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="flex flex-col h-[calc(100vh-140px)] bg-white rounded-2xl shadow-xl border border-stone-200 overflow-hidden"
        >
            {/* Chat Header */}
            <div className={`p-4 border-b border-stone-100 flex items-center justify-between bg-gradient-to-r ${book.color}`}>
                <div className="flex items-center gap-4">
                    <button onClick={onBack} className="p-2 bg-white/50 hover:bg-white rounded-full transition-colors text-stone-600">
                        <ArrowLeft size={20} />
                    </button>
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg overflow-hidden border border-stone-200 shadow-sm">
                            <img src={book.cover} alt="cover" className="w-full h-full object-cover" />
                        </div>
                        <div>
                            <h2 className={`font-serif font-bold text-lg leading-none ${book.text_color}`}>{book.title}</h2>
                            <p className="text-xs text-stone-500 mt-1">AI Teacher Mode</p>
                        </div>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setMessages([{ role: 'assistant', content: 'Namaste. Let us start fresh. What would you like to know?' }])}
                        className="p-2 text-stone-400 hover:text-stone-600 hover:bg-white/50 rounded-full transition-colors"
                        title="Clear Chat"
                    >
                        <RefreshCw size={18} />
                    </button>
                </div>
            </div>

            {/* Chat Area */}
            <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 bg-stone-50/50">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        {msg.role === 'assistant' && (
                            <div className="w-8 h-8 rounded-full bg-vedic-orange/10 flex items-center justify-center text-lg mr-2 mt-2 border border-vedic-orange/20 shrink-0">
                                🧘
                            </div>
                        )}
                        <div className={`max-w-[85%] md:max-w-[70%] rounded-2xl p-4 md:p-5 shadow-sm leading-relaxed text-sm md:text-base ${msg.role === 'user'
                                ? 'bg-vedic-blue text-white rounded-tr-none'
                                : 'bg-white text-stone-700 border border-stone-100 rounded-tl-none'
                            }`}>
                            <ReactMarkdown
                                components={{
                                    p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                                    strong: ({ children }) => <strong className="font-bold text-vedic-orange">{children}</strong>
                                }}
                            >
                                {msg.content}
                            </ReactMarkdown>
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="flex justify-start">
                        <div className="w-8 h-8 rounded-full bg-vedic-orange/10 flex items-center justify-center text-lg mr-2 mt-2 border border-vedic-orange/20 shrink-0">
                            ✨
                        </div>
                        <div className="bg-white p-4 rounded-2xl rounded-tl-none border border-stone-100 flex gap-1 items-center">
                            <span className="w-2 h-2 bg-stone-300 rounded-full animate-bounce"></span>
                            <span className="w-2 h-2 bg-stone-300 rounded-full animate-bounce delay-100"></span>
                            <span className="w-2 h-2 bg-stone-300 rounded-full animate-bounce delay-200"></span>
                        </div>
                    </div>
                )}
            </div>

            {/* Input Area */}
            <div className="p-4 bg-white border-t border-stone-100">
                <form onSubmit={handleSend} className="max-w-4xl mx-auto flex gap-3">
                    <div className="flex-1 relative">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder={`Ask something from ${book.title}...`}
                            className="w-full bg-stone-50 border border-stone-200 rounded-xl px-4 py-4 pr-12 text-stone-700 focus:outline-none focus:ring-2 focus:ring-vedic-orange/20 focus:border-vedic-orange transition-all"
                            disabled={loading}
                        />
                        <div className="absolute right-3 top-1/2 -translate-y-1/2 text-stone-400">
                            <Sparkles size={18} />
                        </div>
                    </div>
                    <button
                        type="submit"
                        disabled={loading || !input.trim()}
                        className="bg-vedic-orange hover:bg-vedic-orange/90 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 rounded-xl font-bold flex items-center gap-2 transition-all shadow-lg hover:shadow-orange-200/50"
                    >
                        Send <Send size={18} />
                    </button>
                </form>
            </div>
        </motion.div>
    );
};

export default LearningPage;
