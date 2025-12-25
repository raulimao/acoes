'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { supabase } from '@/lib/supabase';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

interface User {
    username: string;
    name: string;
    email: string;
    is_premium: boolean;
}

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    loading: boolean;
    error: string | null;
    login: (email: string, password: string) => Promise<boolean>;
    register: (name: string, email: string, password: string) => Promise<boolean>;
    loginWithGoogle: () => Promise<void>;
    logout: () => void;
    clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const router = useRouter();

    // Check auth on mount
    useEffect(() => {
        checkAuth();
    }, []);

    const checkAuth = async () => {
        const token = localStorage.getItem('token');
        if (!token) {
            setLoading(false);
            return;
        }

        try {
            const response = await axios.get(`${API_URL}/auth/me`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setUser(response.data);
        } catch (err) {
            // Token invalid, clear it
            localStorage.removeItem('token');
        } finally {
            setLoading(false);
        }
    };

    const login = async (email: string, password: string): Promise<boolean> => {
        setError(null);
        setLoading(true);

        try {
            const response = await axios.post(`${API_URL}/auth/login`, {
                email,
                password
            });

            const { access_token, user: userData } = response.data;
            localStorage.setItem('token', access_token);
            setUser(userData);
            return true;
        } catch (err: any) {
            const message = err.response?.data?.detail || 'Erro ao fazer login';
            setError(message);
            return false;
        } finally {
            setLoading(false);
        }
    };

    const register = async (name: string, email: string, password: string): Promise<boolean> => {
        setError(null);
        setLoading(true);

        try {
            const response = await axios.post(`${API_URL}/auth/register`, {
                name,
                email,
                password
            });

            const { access_token, user: userData } = response.data;
            localStorage.setItem('token', access_token);
            setUser(userData);
            return true;
        } catch (err: any) {
            const message = err.response?.data?.detail || 'Erro ao criar conta';
            setError(message);
            return false;
        } finally {
            setLoading(false);
        }
    };

    const loginWithGoogle = async () => {
        try {
            const { error } = await supabase.auth.signInWithOAuth({
                provider: 'google',
                options: {
                    redirectTo: `${window.location.origin}/auth/callback`
                }
            });

            if (error) throw error;
            // OAuth flow will redirect, no need to do anything else here
        } catch (err: any) {
            console.error('Google login error:', err);
            setError('Erro ao fazer login com Google');
        }
    };

    const logout = () => {
        localStorage.removeItem('token');
        setUser(null);
        router.push('/login');
    };

    const clearError = () => setError(null);

    return (
        <AuthContext.Provider value={{
            user,
            isAuthenticated: !!user,
            loading,
            error,
            login,
            register,
            loginWithGoogle,
            logout,
            clearError
        }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
