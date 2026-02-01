import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import Input from '../../ui/Input';
import LocationInput from '../../ui/LocationInput';
import VedicButton from '../../ui/VedicButton';
import { toast } from 'react-toastify';

const FamilyMemberModal = ({ isOpen, onClose, onSubmit, initialData = null }) => {
    const [formData, setFormData] = useState({
        name: '',
        relationship: '',
        gender: 'male',
        date_of_birth: '',
        time_of_birth: '',
        location: '',
        latitude: '',
        longitude: '',
        timezone: 'Asia/Kolkata'
    });

    useEffect(() => {
        if (initialData) {
            setFormData(initialData);
        } else {
            setFormData({
                name: '',
                relationship: '',
                gender: 'male',
                date_of_birth: '',
                time_of_birth: '',
                location: '',
                latitude: '',
                longitude: '',
                timezone: 'Asia/Kolkata'
            });
        }
    }, [initialData, isOpen]);

    const handleLocationSelect = (place) => {
        setFormData(prev => ({
            ...prev,
            latitude: place.latitude,
            longitude: place.longitude,
            location: place.display_name
        }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!formData.name || !formData.date_of_birth || !formData.time_of_birth || !formData.latitude) {
            toast.error("Please fill all required fields");
            return;
        }
        onSubmit(formData);
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden"
                >
                    <div className="flex justify-between items-center p-4 border-b border-stone-100 bg-vedic-cream">
                        <h3 className="font-serif font-bold text-lg text-vedic-blue">
                            {initialData ? 'Edit Person' : 'Add New Person'}
                        </h3>
                        <button onClick={onClose} className="p-1 hover:bg-stone-200 rounded-full transition-colors">
                            <X size={20} className="text-stone-500" />
                        </button>
                    </div>

                    <form onSubmit={handleSubmit} className="p-6 space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <Input
                                label="Name"
                                value={formData.name}
                                onChange={e => setFormData({ ...formData, name: e.target.value })}
                                placeholder="Enter Name"
                            />
                            <Input
                                label="Relationship"
                                value={formData.relationship}
                                onChange={e => setFormData({ ...formData, relationship: e.target.value })}
                                placeholder="e.g. Spouse, Father"
                            />
                        </div>

                        <div>
                            <label className="text-xs font-bold text-stone-500 uppercase tracking-wide mb-1 block">Gender</label>
                            <div className="flex gap-2">
                                {['male', 'female', 'other'].map(g => (
                                    <button
                                        type="button"
                                        key={g}
                                        onClick={() => setFormData({ ...formData, gender: g })}
                                        className={`flex-1 py-2 text-sm font-bold border rounded-lg capitalize ${formData.gender === g ? 'bg-vedic-orange text-white border-vedic-orange' : 'bg-white text-stone-500 border-stone-200'}`}
                                    >
                                        {g}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <Input
                                type="date"
                                label="Date of Birth"
                                value={formData.date_of_birth}
                                onChange={e => setFormData({ ...formData, date_of_birth: e.target.value })}
                            />
                            <Input
                                type="time"
                                label="Time of Birth"
                                value={formData.time_of_birth}
                                onChange={e => setFormData({ ...formData, time_of_birth: e.target.value })}
                            />
                        </div>

                        <div className="relative">
                            <LocationInput
                                label="Birth Place"
                                value={formData.location}
                                onChange={e => setFormData({ ...formData, location: e.target.value, latitude: '', longitude: '' })}
                                onLocationSelect={handleLocationSelect}
                                placeholder="Search City..."
                            />
                        </div>

                        <div className="pt-4 flex gap-3">
                            <button
                                type="button"
                                onClick={onClose}
                                className="flex-1 py-3 text-sm font-bold text-stone-500 hover:bg-stone-100 rounded-lg transition-colors"
                            >
                                Cancel
                            </button>
                            <VedicButton type="submit" variant="primary" className="flex-1">
                                {initialData ? 'Update Person' : 'Save Person'}
                            </VedicButton>
                        </div>
                    </form>
                </motion.div>
            </div>
        </AnimatePresence>
    );
};

export default FamilyMemberModal;
