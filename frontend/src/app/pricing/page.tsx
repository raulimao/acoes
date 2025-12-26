'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Check, X, Zap, Crown, Shield } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { useRouter } from 'next/navigation';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export default function PricingPage() {
    const { user, loading } = useAuth();
    const router = useRouter();
    const [isLoadingCheckout, setIsLoadingCheckout] = useState(false);

    const handleSubscribe = async () => {
        if (!user) {
            router.push('/login');
            return;
        }

        setIsLoadingCheckout(true);
        try {
            // Get checkout URL from backend
            const { data } = await axios.post(`${API_URL}/payments/checkout`, {
                return_url: window.location.origin
            }, {
                headers: {
                    Authorization: `Bearer ${localStorage.getItem('token')}`
                }
            });

            // Redirect to Stripe
            window.location.href = data.url;
        } catch (error) {
            console.error('Error creating checkout session:', error);
            alert('Erro ao iniciar pagamento. Tente novamente.');
            setIsLoadingCheckout(false);
        }
    };

    const features = [
        { name: "Análise de Ações", free: true, premium: true },
        { name: "Ranking Bazin/Graham", free: true, premium: true },
        { name: "Batalha de Ações", free: true, premium: true },
        { name: "Scores Avançados", free: false, premium: true },
        { name: "Relatórios PDF", free: false, premium: true },
        { name: "Recomendação IA", free: false, premium: true },
        { name: "Sem Anúncios", free: false, premium: true },
        { name: "Suporte Prioritário", free: false, premium: true },
    ];

    return (
        <div className="min-h-screen bg-gray-900 text-white py-20 px-4">
            <div className="max-w-6xl mx-auto space-y-16">

                {/* Header */}
                <div className="text-center space-y-4">
                    <motion.h1
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-4xl md:text-6xl font-black bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent"
                    >
                        Invista como um Profissional
                    </motion.h1>
                    <p className="text-gray-400 text-xl max-w-2xl mx-auto">
                        Desbloqueie o poder máximo da análise fundamentalista e tome decisões mais inteligentes.
                    </p>
                </div>

                {/* Cards */}
                <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">

                    {/* Free Plan */}
                    <motion.div
                        initial={{ opacity: 0, x: -50 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.1 }}
                        className="bg-gray-800 rounded-2xl p-8 border border-gray-700 flex flex-col"
                    >
                        <div className="mb-8">
                            <h3 className="text-2xl font-bold text-gray-300 mb-2">Basic</h3>
                            <div className="flex items-baseline gap-1">
                                <span className="text-4xl font-bold text-white">R$ 0</span>
                                <span className="text-gray-500">/mês</span>
                            </div>
                            <p className="text-gray-400 mt-4">Para iniciantes que querem começar do jeito certo.</p>
                        </div>

                        <ul className="space-y-4 mb-8 flex-1">
                            {features.map((feature, i) => (
                                <li key={i} className="flex items-center gap-3">
                                    {feature.free ? (
                                        <Check className="w-5 h-5 text-green-500 shrink-0" />
                                    ) : (
                                        <X className="w-5 h-5 text-gray-600 shrink-0" />
                                    )}
                                    <span className={feature.free ? 'text-gray-200' : 'text-gray-500'}>
                                        {feature.name}
                                    </span>
                                </li>
                            ))}
                        </ul>

                        <button
                            disabled
                            className="w-full py-4 rounded-xl font-bold bg-gray-700 text-gray-400 cursor-not-allowed"
                        >
                            Plano Atual
                        </button>
                    </motion.div>

                    {/* Premium Plan */}
                    <motion.div
                        initial={{ opacity: 0, x: 50 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.2 }}
                        className="relative bg-gray-800 rounded-2xl p-8 border-2 border-purple-500 flex flex-col shadow-2xl shadow-purple-900/20"
                    >
                        <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-gradient-to-r from-purple-600 to-pink-600 text-white px-4 py-1 rounded-full text-sm font-bold flex items-center gap-2">
                            <Crown className="w-4 h-4" /> RECOMENDADO
                        </div>

                        <div className="mb-8">
                            <h3 className="text-2xl font-bold text-white mb-2 flex items-center gap-2">
                                <Zap className="w-6 h-6 text-yellow-400" /> Pro
                            </h3>
                            <div className="flex items-baseline gap-1">
                                <span className="text-4xl font-bold text-white">R$ 29,90</span>
                                <span className="text-gray-500">/mês</span>
                            </div>
                            <p className="text-gray-400 mt-4">Tudo o que você precisa para multiplicar seu patrimônio.</p>
                        </div>

                        <ul className="space-y-4 mb-8 flex-1">
                            {features.map((feature, i) => (
                                <li key={i} className="flex items-center gap-3">
                                    {feature.premium ? (
                                        <Check className="w-5 h-5 text-purple-400 shrink-0" />
                                    ) : (
                                        <X className="w-5 h-5 text-gray-600 shrink-0" />
                                    )}
                                    <span className={feature.premium ? 'text-white font-medium' : 'text-gray-500'}>
                                        {feature.name}
                                    </span>
                                </li>
                            ))}
                        </ul>

                        <button
                            onClick={handleSubscribe}
                            disabled={isLoadingCheckout || user?.is_premium}
                            className={`w-full py-4 rounded-xl font-bold transition-all transform hover:scale-105 ${user?.is_premium
                                    ? 'bg-green-600 text-white cursor-default'
                                    : 'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:shadow-lg hover:shadow-purple-500/25'
                                }`}
                        >
                            {isLoadingCheckout ? 'Processando...' : user?.is_premium ? 'Você já é Premium! 👑' : 'Assinar Agora'}
                        </button>
                    </motion.div>

                </div>

                {/* Trust Badges */}
                <div className="flex flex-wrap justify-center gap-8 text-gray-500 mt-12">
                    <div className="flex items-center gap-2">
                        <Shield className="w-5 h-5" /> Pagamento Seguro via Stripe
                    </div>
                </div>
            </div>
        </div>
    );
}
