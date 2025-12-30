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
    resendConfirmation: (email: string) => Promise<boolean>;
    logout: () => void;
    clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const router = useRouter();
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Check for existing session on mount
    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            fetchUser(token);
        } else {
            setLoading(false);
        }
    }, []);

    const fetchUser = async (token: string) => {
        try {
            const { data } = await axios.get(`${API_URL}/auth/me`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setUser(data);
        } catch (err) {
            localStorage.removeItem('token');
        } finally {
            setLoading(false);
        }
    };

    const login = async (email: string, password: string): Promise<boolean> => {
        setError(null);
        try {
            const { data } = await axios.post(`${API_URL}/auth/login`, { email, password });
            localStorage.setItem('token', data.access_token);
            await fetchUser(data.access_token);
            return true;
        } catch (error: unknown) {
            const err = error as any;
            const message = err.response?.data?.detail || 'Erro ao fazer login';
            setError(message);
            return false;
        }
    };

    const register = async (name: string, email: string, password: string): Promise<boolean> => {
        setError(null);
        try {
            await axios.post(`${API_URL}/auth/register`, { name, email, password });
            // After registration, show success message - user needs to confirm email
            setError('Conta criada! Verifique seu email para confirmar.');
            return true;
        } catch (error: unknown) {
            const err = error as any;
            // Handle 202 (Accepted) - email confirmation required
            if (err.response?.status === 202) {
                setError(err.response?.data?.detail || 'Conta criada! Verifique seu email para confirmar.');
                return true;
            }

            // Handle Pydantic validation errors (422 - array of error objects)
            const detail = err.response?.data?.detail;
            let message = 'Erro ao criar conta';

            if (Array.isArray(detail)) {
                // Pydantic returns [{type, loc, msg, input, ctx}, ...]
                const firstError = detail[0];
                if (firstError?.msg) {
                    // Map common Pydantic messages to Portuguese
                    const msgLower = firstError.msg.toLowerCase();
                    if (msgLower.includes('at least') || msgLower.includes('min_length')) {
                        const field = firstError.loc?.[1] || 'campo';
                        if (field === 'name') message = 'Nome deve ter pelo menos 2 caracteres';
                        else if (field === 'password') message = 'Senha deve ter pelo menos 6 caracteres';
                        else if (field === 'email') message = 'Email inválido';
                        else message = `${field}: ${firstError.msg}`;
                    } else {
                        message = firstError.msg;
                    }
                }
            } else if (typeof detail === 'string') {
                message = detail;
            }

            setError(message);
            return false;
        }
    };

    const loginWithGoogle = async () => {
        const { error } = await supabase.auth.signInWithOAuth({
            provider: 'google',
            options: {
                redirectTo: `${window.location.origin}/auth/callback`
            }
        });
        if (error) {
            setError(error.message);
        }
    };

    const resendConfirmation = async (email: string): Promise<boolean> => {
        try {
            await axios.post(`${API_URL}/auth/resend-confirmation`, { email });
            return true;
        } catch (err) {
            console.error("Error resending confirmation:", err);
            return false;
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
            resendConfirmation,
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
