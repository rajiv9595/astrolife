import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { authService } from '../../services/authService';
import { astroService } from '../../services/astroService';
import Input from '../ui/Input'; // Now using new light theme Input
import LocationInput from '../ui/LocationInput';
import VedicButton from '../ui/VedicButton'; // Now using VedicButton
import { User, Mail, Lock, Phone, MapPin, Calendar, Clock, ArrowRight, Check, Search } from 'lucide-react';
import { toast } from 'react-toastify';

const SignupForm = ({ isEmbedded = false }) => {
    const navigate = useNavigate();
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);

    const [formData, setFormData] = useState({
        name: '',
        email: '',
        password: 'password123', // Default for 'Get Kundli' flow if hidden
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
    if (isEmbedded) {
        return (
            <form onSubmit={handleSubmit} className="flex flex-col gap-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Input
                        id="name" label="Name" placeholder="Your Name"
                        value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })}
                    />
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
                </div>

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
                    {loading ? 'Calculating...' : 'Get Kundli Now'}
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
                    id="password" label="Password" type="password"
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
            </form>
        </div>
    );
};

export default SignupForm;
