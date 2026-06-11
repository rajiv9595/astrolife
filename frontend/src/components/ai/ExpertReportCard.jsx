import React, { useState } from 'react';
import { Sparkles, BrainCircuit, Briefcase, Coins, Heart, Activity, ShieldAlert, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { astroService } from '../../services/astroService';
import { toast } from 'react-toastify';

const ExpertReportCard = ({ chartData }) => {
    const [loading, setLoading] = useState(false);
    const [report, setReport] = useState(null);
    const [activeTab, setActiveTab] = useState('personality');

    const generateReport = async () => {
        try {
            setLoading(true);
            const data = await astroService.generateExpertReport(chartData);
            if (data.report) {
                setReport(data.report);
                toast.success("Cosmic analysis complete!");
            } else if (data.error) {
                toast.error(data.error);
            }
        } catch (error) {
            console.error("AI Report Error:", error);
            toast.error("Failed to generate reading. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    const tabs = [
        { id: 'personality', label: 'Personality', icon: BrainCircuit, color: 'indigo' },
        { id: 'career', label: 'Career', icon: Briefcase, color: 'blue' },
        { id: 'wealth', label: 'Wealth', icon: Coins, color: 'emerald' },
        { id: 'love_and_marriage', label: 'Love', icon: Heart, color: 'rose' },
        { id: 'health', label: 'Health', icon: Activity, color: 'teal' },
        { id: 'karmic_remedies', label: 'Remedies', icon: ShieldAlert, color: 'purple' },
    ];

    return (
        <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full bg-gradient-to-br from-indigo-900 via-slate-900 to-purple-900 rounded-2xl p-1 shadow-2xl relative overflow-hidden"
        >
            <div className="bg-white/95 backdrop-blur-xl rounded-xl w-full h-full p-6 relative z-10">
                {!report && !loading ? (
                    <div className="flex flex-col items-center justify-center py-10 text-center">
                        <div className="w-16 h-16 rounded-2xl bg-indigo-50 flex items-center justify-center mb-4">
                            <Sparkles className="w-8 h-8 text-indigo-600" />
                        </div>
                        <h2 className="text-2xl font-serif font-bold text-slate-800 mb-2">Expert AI Life Reading</h2>
                        <p className="text-slate-500 max-w-md mx-auto mb-8 leading-relaxed">
                            Our AI will analyze your Shadbala, Ashtakavarga, Doshas, and Jaimini Karakas to generate a highly accurate, multi-domain reading of your destiny.
                        </p>
                        <button
                            onClick={generateReport}
                            className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-8 rounded-full shadow-lg shadow-indigo-200 transition-all transform hover:scale-105 active:scale-95 flex items-center gap-2"
                        >
                            <Sparkles className="w-5 h-5" />
                            Generate My Reading
                        </button>
                    </div>
                ) : loading ? (
                    <div className="flex flex-col items-center justify-center py-16 text-center">
                        <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                        >
                            <Loader2 className="w-12 h-12 text-indigo-500 mb-4" />
                        </motion.div>
                        <h3 className="text-lg font-bold text-slate-700">Synthesizing Cosmic Data...</h3>
                        <p className="text-sm text-slate-400 mt-2">Analyzing 16 divisional charts and thousands of combinations.</p>
                    </div>
                ) : (
                    <div>
                        <div className="flex items-center gap-3 mb-6 border-b border-slate-100 pb-4">
                            <Sparkles className="w-6 h-6 text-indigo-600" />
                            <h2 className="text-xl font-serif font-bold text-slate-800">Your Master Reading</h2>
                        </div>

                        {/* Tabs */}
                        <div className="flex flex-wrap gap-2 mb-6">
                            {tabs.map(tab => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id)}
                                    className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-sm transition-all ${
                                        activeTab === tab.id 
                                        ? `bg-${tab.color}-100 text-${tab.color}-700 shadow-sm border border-${tab.color}-200` 
                                        : 'bg-slate-50 text-slate-500 hover:bg-slate-100 border border-slate-100'
                                    }`}
                                >
                                    <tab.icon className="w-4 h-4" />
                                    {tab.label}
                                </button>
                            ))}
                        </div>

                        {/* Content */}
                        <AnimatePresence mode="wait">
                            <motion.div
                                key={activeTab}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                className="bg-slate-50 rounded-xl p-6 border border-slate-100"
                            >
                                {activeTab !== 'karmic_remedies' ? (
                                    <div>
                                        <p className="text-slate-700 leading-relaxed mb-6 font-medium">
                                            {report[activeTab]?.summary}
                                        </p>
                                        
                                        {report[activeTab]?.strengths && (
                                            <div className="mb-4">
                                                <h4 className="text-sm font-bold text-indigo-800 uppercase tracking-wider mb-2">Key Strengths</h4>
                                                <ul className="space-y-1">
                                                    {report[activeTab].strengths.map((s, i) => (
                                                        <li key={i} className="flex items-start gap-2 text-slate-600 text-sm">
                                                            <span className="text-indigo-400 font-bold">•</span> {s}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}

                                        {report[activeTab]?.weaknesses && (
                                            <div>
                                                <h4 className="text-sm font-bold text-rose-800 uppercase tracking-wider mb-2 mt-4">Areas for Growth</h4>
                                                <ul className="space-y-1">
                                                    {report[activeTab].weaknesses.map((w, i) => (
                                                        <li key={i} className="flex items-start gap-2 text-slate-600 text-sm">
                                                            <span className="text-rose-400 font-bold">•</span> {w}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}

                                        {report[activeTab]?.favorable_fields && (
                                            <div>
                                                <h4 className="text-sm font-bold text-blue-800 uppercase tracking-wider mb-2">Favorable Fields</h4>
                                                <div className="flex flex-wrap gap-2">
                                                    {report[activeTab].favorable_fields.map((f, i) => (
                                                        <span key={i} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-bold">{f}</span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {report[activeTab]?.financial_yogas_present && (
                                            <div>
                                                <h4 className="text-sm font-bold text-emerald-800 uppercase tracking-wider mb-2">Active Wealth Yogas</h4>
                                                <ul className="space-y-1">
                                                    {report[activeTab].financial_yogas_present.map((y, i) => (
                                                        <li key={i} className="flex items-start gap-2 text-slate-600 text-sm">
                                                            <span className="text-emerald-500 font-bold">💎</span> {y}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}

                                        {report[activeTab]?.partner_traits && (
                                            <div>
                                                <h4 className="text-sm font-bold text-rose-800 uppercase tracking-wider mb-2">Partner Traits</h4>
                                                <p className="text-slate-600 text-sm italic border-l-2 border-rose-200 pl-3 py-1">"{report[activeTab].partner_traits}"</p>
                                            </div>
                                        )}

                                        {report[activeTab]?.vulnerable_areas && (
                                            <div>
                                                <h4 className="text-sm font-bold text-teal-800 uppercase tracking-wider mb-2">Vulnerable Areas</h4>
                                                <div className="flex flex-wrap gap-2">
                                                    {report[activeTab].vulnerable_areas.map((v, i) => (
                                                        <span key={i} className="px-3 py-1 bg-teal-100 text-teal-700 rounded-full text-xs font-bold">{v}</span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <div>
                                        <h4 className="text-sm font-bold text-purple-800 uppercase tracking-wider mb-4 flex items-center gap-2">
                                            <ShieldAlert className="w-4 h-4" /> Recommended Prescriptions
                                        </h4>
                                        <ul className="space-y-3">
                                            {report.karmic_remedies?.map((r, i) => (
                                                <li key={i} className="flex items-start gap-3 bg-white p-3 rounded-lg shadow-sm border border-slate-100">
                                                    <span className="w-6 h-6 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center text-xs font-bold shrink-0">{i+1}</span> 
                                                    <span className="text-slate-700 text-sm pt-0.5">{r}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </motion.div>
                        </AnimatePresence>
                    </div>
                )}
            </div>
            {/* Ambient Background Glow */}
            <div className="absolute -top-24 -right-24 w-64 h-64 bg-indigo-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
            <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
        </motion.div>
    );
};

export default ExpertReportCard;
