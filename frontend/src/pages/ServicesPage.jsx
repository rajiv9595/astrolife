import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Navbar from '../components/ui/Navbar';
import VedicCard from '../components/ui/VedicCard';
import {
    Star, Database, Activity, User, Heart, Bot,
    BookOpen, MessageCircle, Clock, Calendar,
    Search, Award, Trophy, FileText, Cpu, Users
} from 'lucide-react';

const tools = [
    { name: 'Charts', icon: Activity, description: 'View your detailed birth charts (D1, D9, D10).', link: '/dashboard' },
    { name: 'Planets', icon: GlobeIcon, description: 'Detailed planetary positions and degrees.', link: '/tools/planets' },
    { name: 'Dasha Timeline', icon: Clock, description: 'Track your current and future life periods.', link: '/tools/dasha' },
    { name: 'Yogas', icon: Star, description: 'Discover special planetary combinations.', link: '/tools/yogas' },
    { name: 'Your Info', icon: User, description: 'Your personal birth details and settings.', link: '/tools/info' },
    { name: 'Match Checker', icon: Heart, description: 'Check compatibility with a partner.', link: '/match' },
    { name: 'AI Astrologer', icon: Bot, description: 'Chat with our AI for instant insights.', link: '/tools/ai-astrologer' },
    { name: 'AI Guru Teacher', icon: BookOpen, description: 'Learn astrology from an AI tutor.', link: '/learning' },
    { name: 'AI Horary Prasna', icon: MessageCircle, description: 'Ask specific questions and get answers.', link: '/tools/ai-horary' },
    { name: 'Life Predictor', icon: SparklesIcon, description: 'Get predictions about your life path.', link: '/tools/life-predictor' },
    { name: 'Horoscope', icon: SunIcon, description: 'Daily, weekly, and monthly horoscopes.', link: '/tools/horoscope' },
    { name: 'Good Time Finder', icon: Calendar, description: 'Find auspicious times for activities.', link: '/tools/good-time' },
    { name: 'Numerology', icon: HashIcon, description: 'Explore the power of numbers in your life.', link: '/tools/numerology' },
    { name: 'Birth Time Finder', icon: Search, description: 'Rectify and find accurate birth time.', link: '/tools/rectification' },
    { name: 'API Builder', icon: Cpu, description: 'Build your own astrology apps.', link: '/tools/api' },
    { name: 'Famous People', icon: Users, description: 'See charts of famous personalities.', link: '/tools/famous' },
    { name: 'Sports Prediction', icon: Trophy, description: 'Predict outcomes of sports events.', link: '/tools/sports' },
    { name: 'Articles', icon: FileText, description: 'Read latest articles on Vedic astrology.', link: '/blog' },
];

// Helper icons (some might need custom ones or specific lucide imports)
function GlobeIcon(props) {
    return (
        <svg
            {...props}
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <circle cx="12" cy="12" r="10" />
            <line x1="2" x2="22" y1="12" y2="12" />
            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
        </svg>
    )
}

function SparklesIcon(props) {
    return (
        <svg
            {...props}
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z" />
            <path d="M20 3v4" />
            <path d="M22 5h-4" />
            <path d="M4 17v2" />
            <path d="M5 18H3" />
        </svg>
    )
}

function SunIcon(props) {
    return (
        <svg
            {...props}
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2" />
            <path d="M12 20v2" />
            <path d="m4.93 4.93 1.41 1.41" />
            <path d="m17.66 17.66 1.41 1.41" />
            <path d="M2 12h2" />
            <path d="M20 12h2" />
            <path d="m6.34 17.66-1.41 1.41" />
            <path d="m19.07 4.93-1.41 1.41" />
        </svg>
    )
}

function HashIcon(props) {
    return (
        <svg
            {...props}
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <line x1="4" x2="20" y1="9" y2="9" />
            <line x1="4" x2="20" y1="15" y2="15" />
            <line x1="10" x2="8" y1="3" y2="21" />
            <line x1="16" x2="14" y1="3" y2="21" />
        </svg>
    )
}

const ServicesPage = () => {
    const navigate = useNavigate();
    const isAuthenticated = !!localStorage.getItem('token');

    const handleToolClick = (link) => {
        if (link === '/blog') {
            navigate(link);
            return;
        }

        if (isAuthenticated) {
            navigate(link);
        } else {
            // Optional: Show a toast notification here if desired
            // toast.info("Please login to access this tool");
            navigate('/auth');
        }
    };

    return (
        <div className="min-h-screen bg-vedic-cream pb-20">
            <Navbar />

            <main className="max-w-7xl mx-auto px-4 sm:px-6 pt-12 space-y-8">
                <div className="text-center space-y-4">
                    <h1 className="text-4xl font-serif font-bold text-vedic-blue">Our Services</h1>
                    <p className="text-stone-600 max-w-2xl mx-auto">
                        Explore our comprehensive suite of Vedic astrology tools designed to guide you through life's journey.
                    </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {tools.map((tool) => (
                        <div key={tool.name} onClick={() => handleToolClick(tool.link)} className="block group cursor-pointer">
                            <VedicCard className="h-full p-6 flex flex-col items-center text-center hover:shadow-xl transition-all duration-300 border-2 border-transparent hover:border-vedic-orange/20 bg-white">
                                <div className="w-16 h-16 rounded-full bg-vedic-gold/10 flex items-center justify-center text-vedic-orange mb-4 group-hover:scale-110 group-hover:bg-vedic-orange group-hover:text-white transition-all duration-300">
                                    <tool.icon size={32} />
                                </div>
                                <h3 className="text-xl font-serif font-bold text-vedic-blue mb-2 group-hover:text-vedic-orange transition-colors">
                                    {tool.name}
                                </h3>
                                <p className="text-sm text-stone-500 line-clamp-2">
                                    {tool.description}
                                </p>
                            </VedicCard>
                        </div>
                    ))}
                </div>
            </main>
        </div>
    );
};

export default ServicesPage;
