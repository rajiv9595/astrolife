import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GoogleLogin } from '@react-oauth/google';
import { authService } from '../../services/authService';
import Input from '../ui/Input';
import VedicButton from '../ui/VedicButton';
import { User, Lock, ArrowRight } from 'lucide-react';
import { toast } from 'react-toastify';

const LoginForm = () => {
    const [formData, setFormData] = useState({ email: '', password: '' });
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await authService.login(formData.email, formData.password);
            toast.success("Welcome back.");
            navigate('/dashboard');
        } catch (err) {
            toast.error(err.response?.data?.detail || "Login failed");
        } finally {
            setLoading(false);
        }
    };

    const handleGoogleSuccess = async (credentialResponse) => {
        setLoading(true);
        try {
            await authService.googleLogin(credentialResponse.credential);
            toast.success("Welcome.");
            navigate('/dashboard');
        } catch (err) {
            console.error(err);
            toast.error("Google Login failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
            <Input
                id="email"
                label="Username / Email"
                type="email"
                placeholder="Enter your email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                icon={User}
                required
            />
            <Input
                id="password"
                label="Password"
                type="password"
                placeholder="Enter password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                icon={Lock}
                required
            />

            <div className="flex justify-between items-center text-sm">
                <label className="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" className="rounded border-stone-300 text-vedic-orange focus:ring-vedic-orange" />
                    <span className="text-stone-500">Remember me</span>
                </label>
                <a href="#" className="text-vedic-orange font-bold hover:underline">Forgot password?</a>
            </div>

            <VedicButton
                type="submit"
                variant="primary"
                className="w-full mt-2"
                disabled={loading}
            >
                {loading ? 'Authenticating...' : 'Login Now'}
            </VedicButton>

            <div className="mt-4">
                <div className="relative flex items-center justify-center mb-4">
                    <span className="bg-white px-2 text-stone-400 text-xs uppercase tracking-wide">Or continue with</span>
                    <div className="absolute inset-x-0 h-[1px] bg-stone-200 -z-10"></div>
                </div>
                <div className="flex justify-center">
                    <GoogleLogin
                        onSuccess={handleGoogleSuccess}
                        onError={() => toast.error("Google Login Failed")}
                        theme="outline"
                        size="large"
                        width="100%"
                        text="signin_with"
                        shape="rectangular"
                    />
                </div>
            </div>
        </form>
    );
};

export default LoginForm;
