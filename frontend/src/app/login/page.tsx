'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { TrendingUp, Mail, Lock, User, ArrowRight, Sparkles, Eye, EyeOff, AlertCircle, Check } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export default function LoginPage() {
    const router = useRouter();
    const { login, register, loginWithGoogle, resendConfirmation, isAuthenticated, loading: authLoading, error, clearError } = useAuth();
    const [isLogin, setIsLogin] = useState(true);
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [acceptedTerms, setAcceptedTerms] = useState(false);
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        name: ''
    });
    const [validationError, setValidationError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    // Redirect if already authenticated
    useEffect(() => {
        if (isAuthenticated) {
            router.push('/');
        }
    }, [isAuthenticated, router]);

    // Clear error when switching modes
    useEffect(() => {
        clearError();
        setValidationError(null);
        setSuccessMessage(null);
    }, [isLogin]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setValidationError(null);
        setSuccessMessage(null);
        clearError();

        let success: boolean;
        if (isLogin) {
            success = await login(formData.email, formData.password);
        } else {
            if (!acceptedTerms) {
                setValidationError("Você precisa concordar com os Termos de Uso e Política de Privacidade.");
                setLoading(false);
                return;
            }
            success = await register(formData.name, formData.email, formData.password);
        }

        if (success) {
            router.push('/');
        }
        setLoading(false);
    };

    // Show loading while checking auth
    if (authLoading) {
        return (
            <div className="login-page">
                <div className="login-bg" />
                <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    style={{ width: '2rem', height: '2rem', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', borderRadius: '50%' }}
                />
            </div>
        );
    }

    return (
        <div className="login-page">
            {/* Animated Background */}
            <div className="login-bg">
                {/* Animated orbs */}
                <motion.div
                    animate={{
                        x: [0, 100, 0],
                        y: [0, -50, 0],
                        scale: [1, 1.2, 1],
                    }}
                    transition={{ duration: 20, repeat: Infinity, ease: "easeInOut" }}
                    className="login-orb login-orb-violet"
                />
                <motion.div
                    animate={{
                        x: [0, -80, 0],
                        y: [0, 80, 0],
                        scale: [1.2, 1, 1.2],
                    }}
                    transition={{ duration: 15, repeat: Infinity, ease: "easeInOut" }}
                    className="login-orb login-orb-cyan"
                />
                <motion.div
                    animate={{
                        x: [0, 50, 0],
                        y: [0, 100, 0],
                    }}
                    transition={{ duration: 25, repeat: Infinity, ease: "easeInOut" }}
                    className="login-orb login-orb-emerald"
                />

                {/* Grid pattern overlay */}
                <div
                    style={{
                        position: 'absolute',
                        inset: 0,
                        opacity: 0.1,
                        backgroundImage: `radial-gradient(circle at 1px 1px, rgba(255,255,255,0.15) 1px, transparent 0)`,
                        backgroundSize: '40px 40px'
                    }}
                />
            </div>

            {/* Floating particles */}
            <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
                {[10, 25, 40, 55, 70, 85, 15, 35, 60, 80].map((left, i) => (
                    <motion.div
                        key={i}
                        style={{
                            position: 'absolute',
                            width: '4px',
                            height: '4px',
                            background: 'rgba(255, 255, 255, 0.3)',
                            borderRadius: '50%',
                            left: `${left}%`,
                            top: `${(i * 10 + 5) % 100}%`,
                        }}
                        animate={{
                            y: [0, -100, 0],
                            opacity: [0, 1, 0],
                        }}
                        transition={{
                            duration: 5 + (i % 3) * 2,
                            repeat: Infinity,
                            delay: i * 0.5,
                        }}
                    />
                ))}
            </div>

            {/* Login Card */}
            <motion.div
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.6 }}
                className="login-card-wrapper"
            >
                <div className="login-card">
                    {/* Logo */}
                    <motion.div
                        className="login-logo-container"
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                    >
                        <div style={{ position: 'relative' }}>
                            <div className="login-logo-icon">
                                <TrendingUp style={{ width: '1.75rem', height: '1.75rem', color: 'white' }} />
                            </div>
                            <motion.div
                                animate={{ rotate: 360 }}
                                transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
                                style={{ position: 'absolute', inset: '-4px', borderRadius: '0.75rem', border: '1px solid rgba(139, 92, 246, 0.3)' }}
                            />
                        </div>
                        <div>
                            <h1 className="login-logo-title">NorteAcoes</h1>
                            <p className="login-logo-subtitle">Dashboard Fundamentalista</p>
                        </div>
                    </motion.div>

                    {/* Toggle Login/Register */}
                    <div className="login-toggle">
                        <button
                            onClick={() => setIsLogin(true)}
                            className={`login-toggle-btn ${isLogin ? 'active' : ''}`}
                        >
                            Entrar
                        </button>
                        <button
                            onClick={() => setIsLogin(false)}
                            className={`login-toggle-btn ${!isLogin ? 'active' : ''}`}
                        >
                            Cadastrar
                        </button>
                    </div>

                    {/* Error Message */}
                    {(error || validationError) && (
                        <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="login-error"
                        >
                            <AlertCircle style={{ width: '1.25rem', height: '1.25rem', color: '#f87171', flexShrink: 0 }} />
                            <p className="login-error-text">{error || validationError}</p>
                        </motion.div>
                    )}

                    {/* Success Message */}
                    {successMessage && (
                        <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="mb-4 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-center gap-3"
                        >
                            <Check style={{ width: '1.25rem', height: '1.25rem', color: '#10b981', flexShrink: 0 }} />
                            <p className="text-sm text-emerald-200">{successMessage}</p>
                        </motion.div>
                    )}

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="login-form">
                        {/* Name field (only for register) */}
                        {!isLogin && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                            >
                                <label className="login-label">Nome</label>
                                <div className="login-input-wrapper">
                                    <User className="login-input-icon" />
                                    <input
                                        type="text"
                                        id="name"
                                        name="name"
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        placeholder="Seu nome"
                                        className="login-input"
                                    />
                                </div>
                            </motion.div>
                        )}

                        {/* Email field */}
                        <div>
                            <label className="login-label">Email</label>
                            <div className="login-input-wrapper">
                                <Mail className="login-input-icon" />
                                <input
                                    type="email"
                                    id="email"
                                    name="email"
                                    value={formData.email}
                                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                    placeholder="seu@email.com"
                                    className="login-input"
                                    required
                                />
                            </div>
                        </div>

                        {/* Password field */}
                        <div>
                            <label className="login-label">Senha</label>
                            <div className="login-input-wrapper">
                                <Lock className="login-input-icon" />
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    id="password"
                                    name="password"
                                    value={formData.password}
                                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                    placeholder="••••••••"
                                    className="login-input"
                                    style={{ paddingRight: '3rem' }}
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    style={{ position: 'absolute', right: '1rem', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: 'rgba(255,255,255,0.3)', cursor: 'pointer' }}
                                >
                                    {showPassword ? <EyeOff style={{ width: '1.25rem', height: '1.25rem' }} /> : <Eye style={{ width: '1.25rem', height: '1.25rem' }} />}
                                </button>
                            </div>
                        </div>

                        {/* Forgot password */}
                        {isLogin && (
                            <div className="login-forgot">
                                <Link href="/forgot-password" className="login-forgot-btn">
                                    Esqueceu a senha?
                                </Link>
                            </div>
                        )}

                        {/* Terms and Conditions Checkbox (Register only) */}
                        {!isLogin && (
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="flex items-start gap-3 mt-4 mb-2"
                            >
                                <div className="relative flex items-center">
                                    <input
                                        type="checkbox"
                                        id="terms"
                                        checked={acceptedTerms}
                                        onChange={(e) => setAcceptedTerms(e.target.checked)}
                                        className="peer h-4 w-4 cursor-pointer appearance-none rounded border border-gray-500 bg-white/5 checked:border-purple-500 checked:bg-purple-500 transition-all"
                                    />
                                    <Check className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-3 text-white opacity-0 peer-checked:opacity-100 transition-opacity" />
                                </div>
                                <label htmlFor="terms" className="text-xs text-gray-400 cursor-pointer select-none leading-tight">
                                    Li e concordo com os <a href="/terms" target="_blank" className="text-purple-400 hover:text-purple-300 underline underline-offset-2">Termos de Uso</a> e <a href="/privacy" target="_blank" className="text-purple-400 hover:text-purple-300 underline underline-offset-2">Política de Privacidade</a>.
                                </label>
                            </motion.div>
                        )}

                        {/* Submit button */}
                        <motion.button
                            type="submit"
                            disabled={loading}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            className="login-submit"
                        >
                            {loading ? (
                                <motion.div
                                    animate={{ rotate: 360 }}
                                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                                    style={{ width: '1.25rem', height: '1.25rem', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', borderRadius: '50%' }}
                                />
                            ) : (
                                <>
                                    <span>{isLogin ? 'Entrar' : 'Criar conta'}</span>
                                    <ArrowRight style={{ width: '1.25rem', height: '1.25rem' }} />
                                </>
                            )}
                        </motion.button>

                        {/* Resend Confirmation Link (Login Mode Only) */}
                        {isLogin && (
                            <div className="mt-4 text-center">
                                <button
                                    type="button"
                                    onClick={async () => {
                                        setValidationError(null);
                                        setSuccessMessage(null);
                                        if (!formData.email) {
                                            setValidationError("Preencha o campo de email acima.");
                                            return;
                                        }
                                        const sent = await resendConfirmation(formData.email);
                                        if (sent) setSuccessMessage("Email de confirmação reenviado! Verifique sua caixa de entrada.");
                                    }}
                                    className="text-xs text-gray-500 hover:text-purple-400 transition-colors underline decoration-dotted underline-offset-4"
                                >
                                    Não recebeu o email de confirmação? Reenviar
                                </button>
                            </div>
                        )}
                    </form>

                    {/* Divider */}
                    <div className="login-divider">
                        <div className="login-divider-line" />
                        <span className="login-divider-text">ou continue com</span>
                        <div className="login-divider-line" />
                    </div>

                    {/* Social login */}
                    <div className="login-social">
                        <button
                            type="button"
                            onClick={loginWithGoogle}
                            className="login-social-btn"
                            style={{ width: '100%' }}
                        >
                            <svg style={{ width: '1.25rem', height: '1.25rem', flexShrink: 0 }} viewBox="0 0 24 24">
                                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                            </svg>
                            Continuar com Google
                        </button>
                    </div>

                    {/* Bottom badge */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.5 }}
                        className="login-footer"
                    >
                        <Sparkles style={{ width: '0.75rem', height: '0.75rem' }} />
                        <span>Análise fundamentalista powered by AI</span>
                    </motion.div>
                </div>
            </motion.div>
        </div>
    );
}
