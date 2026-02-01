import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { GoogleLogin } from '@react-oauth/google';
import { motion, AnimatePresence } from 'framer-motion';
import { authService } from '../../services/authService';
import { astroService } from '../../services/astroService';
import Input from '../ui/Input';
import LocationInput from '../ui/LocationInput';
import VedicButton from '../ui/VedicButton';
import { User, Mail, Lock, Phone, MapPin, Calendar, Clock, ArrowRight, Check, Search } from 'lucide-react';
import { toast } from 'react-toastify';

const SignupForm = ({ isEmbedded = false, isGuest = false }) => {
    const navigate = useNavigate();
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);

    const [formData, setFormData] = useState({
        name: '',
        email: '',
        password: '',
        mobile_number: '',
        date_of_birth: '',
        time_of_birth: '',
        location: '',
        latitude: '',
        longitude: '',
        timezone: 'Asia/Kolkata',
        gender: 'male'
    });

    const handleLocationSelect = (place) => {
        setFormData(prev => ({
            ...prev,
            latitude: place.latitude,
            longitude: place.longitude,
            location: place.display_name
        }));
        toast.success(`Location found: ${place.display_name}`);
    };

    const handleGuestSubmit = async (e) => {
        e.preventDefault();
        if (!formData.date_of_birth || !formData.time_of_birth || !formData.latitude) {
            toast.error("Please enter a valid birth date, time, and location.");
            return;
        }

        const dobParts = formData.date_of_birth.split("-");
        const timeParts = formData.time_of_birth.split(":");

        const params = {
            year: parseInt(dobParts[0]),
            month: parseInt(dobParts[1]),
            day: parseInt(dobParts[2]),
            hour: parseInt(timeParts[0]),
            minute: parseInt(timeParts[1]),
            tz: formData.timezone,
            lat: parseFloat(formData.latitude),
            lon: parseFloat(formData.longitude),
            planets: ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
        };

        navigate('/free-kundli', { state: { params, name: formData.name } });
    };

    const handleGoogleSuccess = async (credentialResponse) => {
        setLoading(true);
        try {
            const data = await authService.googleLogin(credentialResponse.credential);
            toast.success("Welcome.");

            // Check if birth details are present
            if (!data.user.date_of_birth) {
                navigate('/tools/info');
            } else {
                navigate('/dashboard');
            }
        } catch (err) {
            console.error(err);
            toast.error("Google Signup Failed");
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await authService.signup(formData);
            toast.success("Kundli Generated Successfully!");
            navigate('/dashboard');
        } catch (err) {
            toast.error(err.response?.data?.detail || "Calculation failed");
        } finally {
            setLoading(false);
        }
    };

    // Render a single page grid for the 'Customer Reference' look if embedded
    if (isEmbedded || isGuest) {
        return (
            <form onSubmit={isGuest ? handleGuestSubmit : handleSubmit} className="flex flex-col gap-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Input
                        id="name" label="Name" placeholder="Your Name"
                        value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })}
                    />

                    {!isGuest && (
                        <div className="flex flex-col gap-1.5 w-full">
                            <label className="text-sm font-bold text-vedic-text ml-1 tracking-wide uppercase text-[11px]">Gender</label>
                            <div className="flex gap-2">
                                <button type="button"
                                    onClick={() => setFormData({ ...formData, gender: 'male' })}
                                    className={`flex-1 py-3 border rounded-lg text-sm font-bold ${formData.gender === 'male' ? 'bg-vedic-orange text-white border-vedic-orange' : 'bg-white border-stone-200 text-stone-500'}`}
                                >Male</button>
                                <button type="button"
                                    onClick={() => setFormData({ ...formData, gender: 'female' })}
                                    className={`flex-1 py-3 border rounded-lg text-sm font-bold ${formData.gender === 'female' ? 'bg-vedic-orange text-white border-vedic-orange' : 'bg-white border-stone-200 text-stone-500'}`}
                                >Female</button>
                            </div>
                        </div>
                    )}
                </div>

                {!isGuest && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <Input
                            id="mobile" label="Phone No" placeholder="+91..."
                            value={formData.mobile_number} onChange={e => setFormData({ ...formData, mobile_number: e.target.value })}
                        />
                        <Input
                            id="email" label="Email" placeholder="you@email.com"
                            value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })}
                        />
                    </div>
                )}

                <div className="p-4 bg-vedic-beige/50 rounded-lg border border-stone-200 grid grid-cols-2 gap-4">
                    <div className="col-span-2 text-xs font-bold text-vedic-blue uppercase tracking-wide mb-1">Birth Details</div>
                    <Input
                        id="date" type="date"
                        value={formData.date_of_birth} onChange={e => setFormData({ ...formData, date_of_birth: e.target.value })}
                    />
                    <Input
                        id="time" type="time"
                        value={formData.time_of_birth} onChange={e => setFormData({ ...formData, time_of_birth: e.target.value })}
                    />
                    <div className="col-span-2 relative">
                        <LocationInput
                            label="Location"
                            placeholder="Enter Birth Place"
                            value={formData.location}
                            onChange={(e) => setFormData({ ...formData, location: e.target.value, latitude: '', longitude: '' })}
                            onLocationSelect={handleLocationSelect}
                        />
                    </div>
                </div>

                <VedicButton type="submit" variant="primary" className="w-full !py-4 text-lg shadow-lg">
                    {loading ? 'Calculating...' : (isGuest ? 'Get Free Kundli' : 'Register & Get Kundli')}
                </VedicButton>
            </form>
        );
    }

    // Original Multi-Step (fallback for /auth page usage if kept)
    return (
        <div className="w-full">
            <form onSubmit={handleSubmit} className="flex flex-col gap-6">
                <Input
                    id="name" label="Name" placeholder="Your Name"
                    value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })}
                />
                <Input
                    id="email" label="Email" placeholder="you@email.com"
                    value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })}
                />
                <Input
                    id="password" label="Password" type="password" autoComplete="new-password"
                    value={formData.password} onChange={e => setFormData({ ...formData, password: e.target.value })}
                />
                <div className="bg-stone-50 p-4 rounded-lg">
                    <h4 className="font-bold text-sm mb-2">Birth Details</h4>
                    <div className="grid grid-cols-2 gap-2 mb-2">
                        <Input type="date" value={formData.date_of_birth} onChange={e => setFormData({ ...formData, date_of_birth: e.target.value })} />
                        <Input type="time" value={formData.time_of_birth} onChange={e => setFormData({ ...formData, time_of_birth: e.target.value })} />
                    </div>
                    <LocationInput
                        placeholder="Location"
                        value={formData.location}
                        onChange={(e) => setFormData({ ...formData, location: e.target.value, latitude: '', longitude: '' })}
                        onLocationSelect={handleLocationSelect}
                    />
                </div>
                <VedicButton type="submit" variant="primary">Register</VedicButton>

                <div className="mt-4">
                    <div className="relative flex items-center justify-center mb-4">
                        <span className="bg-white px-2 text-stone-400 text-xs uppercase tracking-wide">Or join with</span>
                        <div className="absolute inset-x-0 h-[1px] bg-stone-200 -z-10"></div>
                    </div>
                    <div className="flex justify-center">
                        <GoogleLogin
                            onSuccess={handleGoogleSuccess}
                            onError={() => toast.error("Google Signup Failed")}
                            theme="outline"
                            size="large"
                            width="100%"
                            text="signup_with"
                            shape="rectangular"
                        />
                    </div>
                </div>
            </form>
        </div>
    );
};

export default SignupForm;
