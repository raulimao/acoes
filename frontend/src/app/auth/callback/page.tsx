'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export default function AuthCallback() {
    const router = useRouter();

    useEffect(() => {
        const handleCallback = async () => {
            try {
                // Get session from Supabase
                const { data: { session }, error } = await supabase.auth.getSession();

                if (error) throw error;

                if (session?.user) {
                    // User authenticated with Google
                    const googleUser = session.user;

                    // Register/login in local backend using OAuth endpoint
                    try {
                        const response = await axios.post(`${API_URL}/auth/oauth-login`, null, {
                            params: {
                                email: googleUser.email!,
                                name: googleUser.user_metadata.full_name || googleUser.email?.split('@')[0],
                                provider: 'google'
                            }
                        });

                        localStorage.setItem('token', response.data.access_token);
                        // Use window.location instead of router.push to force full reload
                        // This ensures AuthContext re-checks the token
                        window.location.href = '/';
                    } catch (oauthError: any) {
                        console.error('OAuth sync error:', oauthError);
                        throw new Error('Erro ao sincronizar com backend');
                    }
                } else {
                    throw new Error('No session found');
                }
            } catch (err) {
                console.error('Auth callback error:', err);
                router.push('/login?error=auth_failed');
            }
        };

        handleCallback();
    }, [router]);

    return (
        <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100vh',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
        }}>
            <div style={{ textAlign: 'center', color: 'white' }}>
                <div style={{
                    width: '50px',
                    height: '50px',
                    border: '3px solid rgba(255,255,255,0.3)',
                    borderTopColor: 'white',
                    borderRadius: '50%',
                    margin: '0 auto 20px',
                    animation: 'spin 1s linear infinite'
                }} />
                <p style={{ fontSize: '18px', fontWeight: 500 }}>Autenticando...</p>
            </div>
            <style>{`
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
            `}</style>
        </div>
    );
}
