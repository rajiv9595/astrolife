import React, { useEffect, useState } from 'react';
import { authService } from '../services/authService';
import VedicButton from '../components/ui/VedicButton';
import Input from '../components/ui/Input';
import LocationInput from '../components/ui/LocationInput';
import {
    User, Mail, Phone, Calendar, Clock, MapPin, Globe,
    Edit2, Save, X, Camera, Sparkles, MoveLeft
} from 'lucide-react';
import { toast } from 'react-toastify';
import { useNavigate } from 'react-router-dom';

const ProfileInfoPage = () => {
    const navigate = useNavigate();
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isEditing, setIsEditing] = useState(false);
    const [formData, setFormData] = useState({});
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        const fetchUser = async () => {
            try {
                const data = await authService.getCurrentUser();
                setUser(data);
                setFormData(data);

                // If birth details are missing (e.g. from Google Login), auto-enable edit mode
                if (!data.date_of_birth) {
                    setIsEditing(true);
                    toast.info("Please set your birth details to continue.");
                }
            } catch (error) {
                console.error("Failed to fetch user", error);
                if (error.response && error.response.status === 401) {
                    toast.error("Session expired. Please login again.");
                    authService.logout();
                    navigate('/auth');
                } else {
                    setError("Failed to load profile. " + (error.message || "Unknown error"));
                }
            } finally {
                setLoading(false);
            }
        };
        fetchUser();
    }, [navigate]);

    const handleEditToggle = () => {
        setFormData(user);
        setIsEditing(true);
    };

    const handleCancel = () => {
        setIsEditing(false);
        setFormData(user);
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            const updatedUser = await authService.updateProfile(formData);
            setUser(updatedUser);
            setIsEditing(false);
            toast.success("Profile updated successfully!");
        } catch (error) {
            console.error(error);
            toast.error(error.response?.data?.detail || "Failed to update profile");
        } finally {
            setSaving(false);
        }
    };

    const handleLocationSelect = (place) => {
        setFormData(prev => ({
            ...prev,
            latitude: place.latitude,
            longitude: place.longitude,
            location: place.display_name
        }));
    };

    if (loading) return (
        <div className="flex items-center justify-center min-h-[60vh]">
            <div className="w-12 h-12 border-4 border-vedic-orange border-t-transparent rounded-full animate-spin" />
        </div>
    );

    if (!user) return (
        <div className="flex flex-col items-center justify-center p-10 text-stone-500 gap-4">
            <div className="text-xl font-bold">Unable to load profile</div>
            <div className="text-sm text-red-500 bg-red-50 px-4 py-2 rounded-lg">{error || "User data not found"}</div>
            <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-vedic-orange text-white rounded-lg hover:bg-orange-600 transition-colors"
            >
                Retry
            </button>
        </div>
    );

    // Helper to format date nicely
    const formatDate = (dateString) => {
        if (!dateString) return '--';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { day: 'numeric', month: 'long', year: 'numeric' });
    };

    // New Design Render
    return (
        <div className="max-w-3xl mx-auto animate-fade-in pb-20">
            {/* Nav Back - Optional cleaner look implies removing clutter, but UX needs back button usually. 
                Assuming Layout handles top nav, but let's add a breadcrumb-ish back if needed.
                Here strictly focusing on the Profile Card. 
            */}

            <div className="bg-white rounded-[2rem] shadow-xl overflow-hidden border border-stone-100 relative">

                {/* Decorative Top Banner */}
                <div className="h-48 bg-gradient-to-r from-vedic-orange via-orange-400 to-vedic-gold relative">
                    <div className="absolute inset-0 opacity-10 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')]"></div>
                    <div className="absolute bottom-4 right-6 text-white/80 font-serif italic text-lg opacity-50">
                        "Your celestial signature"
                    </div>
                </div>

                {/* Main Content Container with negative margin to pull avatar up */}
                <div className="px-8 pb-10 relative">

                    {/* Header Section: Avatar & Edit Button */}
                    <div className="flex justify-between items-end -mt-16 mb-8">
                        <div className="relative group">
                            <div className="w-32 h-32 rounded-full border-4 border-white shadow-lg bg-stone-100 flex items-center justify-center text-5xl font-serif text-vedic-blue overflow-hidden">
                                {user.name?.charAt(0)}
                            </div>
                            {/* <button className="absolute bottom-1 right-1 bg-stone-800 text-white p-2 rounded-full shadow-md hover:bg-black transition-colors" title="Change Photo">
                                <Camera size={14} />
                            </button> */}
                        </div>

                        <div className="mb-2">
                            {!isEditing ? (
                                <button
                                    onClick={handleEditToggle}
                                    className="flex items-center gap-2 px-6 py-2.5 bg-vedic-blue text-white rounded-full font-bold text-sm hover:bg-blue-900 transition-all shadow-md active:scale-95"
                                >
                                    <Edit2 size={16} /> <span>Edit Profile</span>
                                </button>
                            ) : (
                                <div className="flex gap-3">
                                    <button
                                        onClick={handleCancel}
                                        className="px-5 py-2.5 rounded-full text-stone-600 font-bold hover:bg-stone-100 transition-colors"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        onClick={handleSave}
                                        disabled={saving}
                                        className="flex items-center gap-2 px-6 py-2.5 bg-vedic-orange text-white rounded-full font-bold text-sm hover:bg-orange-600 transition-all shadow-md active:scale-95"
                                    >
                                        {saving ? 'Saving...' : <><Save size={16} /> Save Changes</>}
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Content Logic: View vs Edit */}
                    {isEditing ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
                            <div className="md:col-span-2">
                                <h3 className="text-sm font-bold text-stone-400 uppercase tracking-wider mb-4 border-b border-stone-100 pb-2">Personal Identity</h3>
                            </div>

                            <Input
                                label="Full Name"
                                value={formData.name || ''}
                                onChange={e => setFormData({ ...formData, name: e.target.value })}
                            />
                            <Input
                                label="Email"
                                value={formData.email || ''}
                                onChange={e => setFormData({ ...formData, email: e.target.value })}
                            />
                            <Input
                                label="Phone Number"
                                value={formData.mobile_number || ''}
                                onChange={e => setFormData({ ...formData, mobile_number: e.target.value })}
                            />

                            <div className="md:col-span-2 mt-4">
                                <h3 className="text-sm font-bold text-stone-400 uppercase tracking-wider mb-4 border-b border-stone-100 pb-2">Birth Details (Used for Charts)</h3>
                            </div>

                            <Input
                                label="Date of Birth"
                                type="date"
                                value={formData.date_of_birth || ''}
                                onChange={e => setFormData({ ...formData, date_of_birth: e.target.value })}
                            />
                            <Input
                                label="Time of Birth"
                                type="time"
                                value={formData.time_of_birth || ''}
                                onChange={e => setFormData({ ...formData, time_of_birth: e.target.value })}
                            />
                            <div className="md:col-span-2">
                                <LocationInput
                                    label="Place of Birth"
                                    value={formData.location || ''}
                                    onChange={(e) => setFormData({ ...formData, location: e.target.value, latitude: '', longitude: '' })}
                                    onLocationSelect={handleLocationSelect}
                                    placeholder="City, Country"
                                />
                            </div>
                            <Input
                                label="Timezone"
                                value={formData.timezone || 'Asia/Kolkata'}
                                onChange={e => setFormData({ ...formData, timezone: e.target.value })}
                            />
                        </div>
                    ) : (
                        <div className="space-y-8 animate-in float-in-bottom duration-500">

                            {/* User Header Info */}
                            <div>
                                <h1 className="text-3xl font-serif font-bold text-vedic-blue mb-1">{user.name}</h1>
                                <div className="flex items-center gap-2 text-stone-500 text-sm font-medium">
                                    <span className="bg-vedic-orange/10 text-vedic-orange px-2 py-0.5 rounded-md text-xs font-bold uppercase tracking-wide">Premium</span>
                                    <span>•</span>
                                    <span>{user.email}</span>
                                </div>
                            </div>

                            {/* Separator */}
                            <hr className="border-stone-100" />

                            {/* Details Grid - Clean & Minimal */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-y-8 gap-x-12">

                                {/* Column 1: Contact */}
                                <div className="space-y-6">
                                    <h3 className="text-xs font-bold text-stone-400 uppercase tracking-widest flex items-center gap-2">
                                        <User size={14} /> Contact Info
                                    </h3>
                                    <div className="space-y-4">
                                        <InfoItem icon={Mail} label="Email Address" value={user.email} />
                                        <InfoItem icon={Phone} label="Mobile Number" value={user.mobile_number} />
                                    </div>
                                </div>

                                {/* Column 2: Birth Data */}
                                <div className="space-y-6">
                                    <h3 className="text-xs font-bold text-vedic-orange uppercase tracking-widest flex items-center gap-2">
                                        <Sparkles size={14} /> Birth Configuration
                                    </h3>
                                    <div className="space-y-4">
                                        <div className="grid grid-cols-2 gap-4">
                                            <InfoItem icon={Calendar} label="Date" value={formatDate(user.date_of_birth)} />
                                            <InfoItem icon={Clock} label="Time" value={user.time_of_birth} />
                                        </div>
                                        <InfoItem icon={MapPin} label="Place of Birth" value={user.location} />
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="pl-9">
                                                <div className="text-[10px] uppercase font-bold text-stone-400">Timezone</div>
                                                <div className="text-stone-700 font-medium text-sm">{user.timezone}</div>
                                            </div>
                                            <div className="pl-4">
                                                <div className="text-[10px] uppercase font-bold text-stone-400">Coords</div>
                                                <div className="text-stone-700 font-medium text-sm flex gap-2">
                                                    <span>{parseFloat(user.latitude || 0).toFixed(2)}N</span>
                                                    <span>{parseFloat(user.longitude || 0).toFixed(2)}E</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Bottom Note */}
            <div className="text-center mt-8 text-stone-400 text-xs max-w-lg mx-auto leading-relaxed">
                Your birth details are used to generate all astrological charts.
                Keep this information accurate for the best predictions.
                <br /> Protected by LifePath Privacy Policy.
            </div>
        </div>
    );
};

// Stylish minimal item row
const InfoItem = ({ icon: Icon, label, value }) => (
    <div className="flex items-start gap-4 group">
        <div className="w-8 h-8 rounded-full bg-stone-50 text-stone-400 group-hover:bg-vedic-blue/5 group-hover:text-vedic-blue transition-colors flex items-center justify-center shrink-0">
            <Icon size={16} />
        </div>
        <div>
            <div className="text-[10px] uppercase font-bold text-stone-400 tracking-wide mb-0.5">{label}</div>
            <div className="text-stone-800 font-serif font-medium text-lg leading-tight group-hover:text-vedic-orange transition-colors">
                {value || <span className="text-stone-300 italic">Not set</span>}
            </div>
        </div>
    </div>
);

export default ProfileInfoPage;
