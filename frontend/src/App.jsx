import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'

import LandingPage from './pages/LandingPage'
import AuthPage from './pages/AuthPage'
import BirthInputPage from './pages/BirthInputPage'
import DashboardPage from './pages/DashboardPage'
import MatchPage from './pages/MatchPage'
import ServicesPage from './pages/ServicesPage'
import LearningPage from './pages/LearningPage'
import DashaPage from './pages/DashaPage'
import ToolsLayout from './components/layout/ToolsLayout'
import AIAstrologerPage from './pages/AIAstrologerPage'
import BlogPage from './pages/BlogPage'
import AboutPage from './pages/AboutPage'
import PlanetsPage from './pages/PlanetsPage'
import YogasPage from './pages/YogasPage'
import ProfileInfoPage from './pages/ProfileInfoPage'
import GuestKundliPage from './pages/GuestKundliPage'

// Protected Route Component
const ProtectedRoute = ({ children }) => {
    const isAuthenticated = localStorage.getItem('token');
    if (!isAuthenticated) {
        return <Navigate to="/auth" replace />;
    }
    return children;
};

function App() {
    return (
        <Router>
            <div className="min-h-screen bg-cosmic-black text-white selection:bg-nebula-purple selection:text-white">
                <AnimatePresence mode="wait">
                    <Routes>
                        <Route path="/" element={<LandingPage />} />
                        <Route path="/auth" element={<AuthPage />} />
                        <Route path="/free-kundli" element={<GuestKundliPage />} />

                        <Route path="/enter-details" element={
                            <ProtectedRoute>
                                <BirthInputPage />
                            </ProtectedRoute>
                        } />
                        <Route path="/dashboard" element={
                            <ProtectedRoute>
                                <DashboardPage />
                            </ProtectedRoute>
                        } />
                        <Route path="/match" element={
                            <ProtectedRoute>
                                <MatchPage />
                            </ProtectedRoute>
                        } />
                        <Route path="/services" element={<ServicesPage />} />
                        <Route path="/learning" element={<LearningPage />} />
                        <Route path="/blog" element={<BlogPage />} />
                        <Route path="/about" element={<AboutPage />} />

                        {/* Tools Routes */}
                        <Route path="/tools" element={
                            <ProtectedRoute>
                                <ToolsLayout />
                            </ProtectedRoute>
                        }>
                            <Route path="dasha" element={<DashaPage />} />
                            <Route path="planets" element={<PlanetsPage />} />
                            <Route path="yogas" element={<YogasPage />} />
                            <Route path="ai-astrologer" element={<AIAstrologerPage />} />
                            <Route path="info" element={<ProfileInfoPage />} />
                            <Route path="*" element={<div className="p-8 text-stone-500">Tool coming soon...</div>} />
                        </Route>

                        <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>
                </AnimatePresence>
            </div>
        </Router>
    )
}

export default App
