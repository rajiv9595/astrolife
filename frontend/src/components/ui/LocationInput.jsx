import React, { useState, useEffect, useRef } from 'react';
import { MapPin, Search, Loader2 } from 'lucide-react';
import { astroService } from '../../services/astroService';
import classNames from 'classnames';

const LocationInput = ({ label, value, onChange, onLocationSelect, error, placeholder = "Search for a city..." }) => {
    const [suggestions, setSuggestions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [showDropdown, setShowDropdown] = useState(false);
    const wrapperRef = useRef(null);

    // Debounce search
    useEffect(() => {
        const timer = setTimeout(async () => {
            if (value && value.length > 2 && showDropdown) {
                setLoading(true);
                try {
                    const results = await astroService.getLocationSuggestions(value);
                    setSuggestions(results);
                } catch (e) {
                    console.error("Failed to fetch suggestions", e);
                } finally {
                    setLoading(false);
                }
            } else if (value.length <= 2) {
                setSuggestions([]);
            }
        }, 300);

        return () => clearTimeout(timer);
    }, [value, showDropdown]);

    // Handle outside click to close dropdown
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
                setShowDropdown(false);
            }
        };

        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [wrapperRef]);

    const handleSelect = (place) => {
        onLocationSelect(place);
        setShowDropdown(false); // Close dropdown
        setSuggestions([]); // Clear suggestions
    };

    const handleInputChange = (e) => {
        onChange(e);
        setShowDropdown(true);
    };

    return (
        <div className="flex flex-col gap-1.5 w-full relative" ref={wrapperRef}>
            {label && (
                <label className="text-sm font-bold text-vedic-text ml-1 tracking-wide uppercase text-[11px] text-stone-500">
                    {label}
                </label>
            )}
            <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-vedic-muted">
                    <MapPin size={18} className="text-stone-400" />
                </div>
                <input
                    type="text"
                    className={classNames(
                        "w-full bg-white border border-stone-300 rounded-lg pl-10 pr-10 py-3 text-stone-900 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-vedic-orange focus:border-transparent transition-all hover:border-vedic-orange shadow-sm font-medium",
                        error && "border-red-500 focus:ring-red-200"
                    )}
                    placeholder={placeholder}
                    value={value}
                    onChange={handleInputChange}
                    autoComplete="off"
                />
                <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                    {loading ? (
                        <Loader2 size={18} className="animate-spin text-vedic-orange" />
                    ) : (
                        <Search size={18} className="text-stone-400" />
                    )}
                </div>
            </div>

            {/* Dropdown Suggestions */}
            {showDropdown && suggestions.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-2xl border border-stone-100 max-h-60 overflow-y-auto z-50 animate-in fade-in zoom-in-95 duration-200">
                    <ul className="py-2">
                        {suggestions.map((place, idx) => (
                            <li
                                key={idx}
                                onClick={() => handleSelect(place)}
                                className="px-4 py-3 hover:bg-vedic-orange/10 cursor-pointer flex items-center gap-3 transition-colors border-b border-stone-50 last:border-0"
                            >
                                <div className="bg-stone-100 p-2 rounded-full text-stone-500">
                                    <MapPin size={16} />
                                </div>
                                <div className="flex flex-col">
                                    <span className="font-medium text-stone-800 text-sm line-clamp-1">{place.display_name.split(',')[0]}</span>
                                    <span className="text-xs text-stone-500 line-clamp-1">{place.display_name}</span>
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {/* No validation or error message included here as it might be handled by parent or just 'required' */}
            {error && (
                <span className="text-xs text-red-500 ml-1 mt-0.5 font-medium">{error}</span>
            )}
        </div>
    );
};

export default LocationInput;
