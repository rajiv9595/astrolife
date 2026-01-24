import React, { useState, useEffect, useRef } from 'react';
import Navbar from '../components/ui/Navbar';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, MessageCircle, ChevronRight, PlayCircle, Lock, Send, Sparkles, X } from 'lucide-react';
import api from '../services/api';
import ReactMarkdown from 'react-markdown';
import { toast } from 'react-toastify';

const LearningPage = () => {
    const [modules, setModules] = useState([]);
    const [activeModule, setActiveModule] = useState(null);
    const [activeLesson, setActiveLesson] = useState(null);
    const [showChat, setShowChat] = useState(false);

    // Fetch Modules
    useEffect(() => {
        const fetchModules = async () => {
            try {
                const res = await api.get('/learn/modules');
                setModules(res.data);
                // Default open first
                if (res.data.length > 0) {
                    setActiveModule(res.data[0]);
                    if (res.data[0].lessons.length > 0) {
                        setActiveLesson(res.data[0].lessons[0]);
                    }
                }
            } catch (err) {
                console.error(err);
                toast.error("Failed to load course content.");
            }
        };
        fetchModules();
    }, []);

    return (
        <div className="min-h-screen bg-stone-50 flex flex-col">
            <Navbar />

            <div className="flex-1 flex max-w-7xl mx-auto w-full pt-6 px-4 md:px-0 gap-6 h-[calc(100vh-100px)]">

                {/* specialized Sidebar - Modules List */}
                <div className="w-80 bg-white rounded-2xl shadow-sm border border-stone-200 overflow-y-auto hidden md:block">
                    <div className="p-6 border-b border-stone-100 bg-vedic-blue text-white sticky top-0 z-10">
                        <h2 className="text-xl font-serif font-bold flex items-center gap-2">
                            <BookOpen size={20} /> Curriculum
                        </h2>
                        <p className="text-xs text-white/70 mt-1">Beginner to Advance</p>
                    </div>
                    <div className="p-4 space-y-4">
                        {modules.map((module, idx) => (
                            <div key={module.id} className="space-y-2">
                                <div
                                    className={`text-xs font-bold uppercase tracking-wider px-2 ${activeModule?.id === module.id ? 'text-vedic-orange' : 'text-stone-400'}`}
                                >
                                    Module {idx + 1}
                                </div>
                                <div className="space-y-1">
                                    {module.lessons.map((lesson, lIdx) => (
                                        <button
                                            key={lesson.id}
                                            onClick={() => {
                                                setActiveModule(module);
                                                setActiveLesson(lesson);
                                            }}
                                            className={`w-full text-left p-3 rounded-lg text-sm font-medium transition-all flex items-center justify-between group ${activeLesson?.id === lesson.id
                                                    ? 'bg-vedic-orange/10 text-vedic-orange border border-vedic-orange/20'
                                                    : 'text-stone-600 hover:bg-stone-50'
                                                }`}
                                        >
                                            <span className="truncate">{lIdx + 1}. {lesson.title}</span>
                                            {activeLesson?.id === lesson.id && <PlayCircle size={14} className="shrink-0" />}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Main Content - Lesson Viewer */}
                <div className="flex-1 bg-white rounded-2xl shadow-sm border border-stone-200 overflow-hidden flex flex-col relative">
                    {activeLesson ? (
                        <>
                            {/* Lesson Header */}
                            <div className="p-8 border-b border-stone-100 pb-6">
                                <div className="text-xs font-bold text-vedic-orange uppercase tracking-wider mb-2">
                                    {activeModule?.title}
                                </div>
                                <h1 className="text-3xl font-serif font-bold text-vedic-blue">{activeLesson.title}</h1>
                            </div>

                            {/* Lesson Content Area */}
                            <div className="p-8 overflow-y-auto flex-1 prose prose-stone max-w-none">
                                <p className="text-lg leading-relaxed text-stone-700">
                                    {activeLesson.content}
                                </p>
                                {/* Placeholder for more rich text content if we had Markdown in JSON */}
                                <div className="mt-8 p-6 bg-vedic-cream rounded-xl border border-vedic-gold/20">
                                    <h4 className="font-bold text-vedic-blue mb-2 flex items-center gap-2">
                                        <Sparkles size={16} className="text-vedic-gold" /> Key Takeaway
                                    </h4>
                                    <p className="text-sm text-stone-600 italic">
                                        "Astrology is a language. Use this lesson to build your vocabulary of the stars."
                                    </p>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="flex-1 flex items-center justify-center flex-col text-stone-400">
                            <BookOpen size={48} className="mb-4 opacity-20" />
                            <p>Select a lesson to begin learning</p>
                        </div>
                    )}

                    {/* Floating Guru Chat Trigger */}
                    <div className="absolute bottom-6 right-6">
                        <button
                            onClick={() => setShowChat(!showChat)}
                            className="bg-vedic-blue text-white p-4 rounded-full shadow-xl hover:scale-105 transition-transform flex items-center gap-2 pr-6 group"
                        >
                            <div className="w-8 h-8 rounded-full bg-vedic-orange flex items-center justify-center">
                                <Sparkles size={16} className="animate-pulse" />
                            </div>
                            <div className="text-left">
                                <span className="block text-xs font-bold text-white/70 uppercase">AI Mentor</span>
                                <span className="block font-serif font-bold leading-none">Ask Guru-ji</span>
                            </div>
                        </button>
                    </div>

                    {/* Chat Interface Overlay */}
                    <AnimatePresence>
                        {showChat && (
                            <motion.div
                                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.95 }}
                                transition={{ duration: 0.2 }}
                                className="absolute bottom-24 right-6 w-96 h-[500px] bg-white rounded-2xl shadow-2xl border border-stone-200 flex flex-col overflow-hidden z-20"
                            >
                                <GuruChat
                                    onClose={() => setShowChat(false)}
                                    activeModuleId={activeModule?.id}
                                    activeLessonId={activeLesson?.id}
                                />
                            </motion.div>
                        )}
                    </AnimatePresence>

                </div>
            </div>
        </div>
    );
};

// --- Guru Chat Component ---
const GuruChat = ({ onClose, activeModuleId, activeLessonId }) => {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: 'Namaste! I am your AI Guru. Do you have any doubts about this lesson?' }
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
                current_module_id: activeModuleId,
                current_lesson_id: activeLessonId
            });

            setMessages(prev => [...prev, { role: 'assistant', content: res.data.reply }]);
        } catch (err) {
            setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I am meditating right now. Please try again later.' }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full font-sans">
            {/* Header */}
            <div className="bg-vedic-blue p-4 flex justify-between items-center text-white">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full border border-white/20 bg-vedic-orange/20 flex items-center justify-center">
                        <span className="text-lg">🧘</span>
                    </div>
                    <div>
                        <h3 className="font-serif font-bold text-sm">AI Guru-ji</h3>
                        <div className="flex items-center gap-1 text-[10px] text-green-400">
                            <span className="w-1.5 h-1.5 rounded-full bg-green-400"></span> Online
                        </div>
                    </div>
                </div>
                <button onClick={onClose} className="text-white/70 hover:text-white"><X size={18} /></button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-stone-50" ref={scrollRef}>
                {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div
                            className={`max-w-[85%] rounded-2xl p-3 text-sm leading-relaxed shadow-sm ${msg.role === 'user'
                                    ? 'bg-vedic-blue text-white rounded-br-none'
                                    : 'bg-white text-stone-700 border border-stone-100 rounded-bl-none'
                                }`}
                        >
                            <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-white rounded-2xl rounded-bl-none p-3 border border-stone-100 shadow-sm flex gap-1">
                            <span className="w-1.5 h-1.5 bg-stone-400 rounded-full animate-bounce"></span>
                            <span className="w-1.5 h-1.5 bg-stone-400 rounded-full animate-bounce delay-100"></span>
                            <span className="w-1.5 h-1.5 bg-stone-400 rounded-full animate-bounce delay-200"></span>
                        </div>
                    </div>
                )}
            </div>

            {/* Input */}
            <form onSubmit={handleSend} className="p-3 bg-white border-t border-stone-200 flex gap-2">
                <input
                    type="text"
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    placeholder="Ask a doubt..."
                    className="flex-1 bg-stone-100 rounded-full px-4 text-sm focus:outline-none focus:ring-1 focus:ring-vedic-orange"
                />
                <button
                    disabled={loading}
                    type="submit"
                    className="bg-vedic-orange text-white w-10 h-10 rounded-full flex items-center justify-center hover:bg-orange-600 disabled:opacity-50"
                >
                    <Send size={16} />
                </button>
            </form>
        </div>
    );
};

export default LearningPage;
