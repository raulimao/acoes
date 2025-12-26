'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Check, X, Zap, Crown, Shield, Star, HelpCircle, ChevronDown } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { useRouter } from 'next/navigation';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export default function PricingPage() {
    const { user } = useAuth();
    const router = useRouter();
    const [isLoadingCheckout, setIsLoadingCheckout] = useState(false);
    const [openFaq, setOpenFaq] = useState<number | null>(null);

    const handleSubscribe = async () => {
        if (!user) {
            router.push('/login');
            return;
        }

        setIsLoadingCheckout(true);
        try {
            const { data } = await axios.post(`${API_URL}/payments/checkout`, {
                return_url: window.location.origin
            }, {
                headers: {
                    Authorization: `Bearer ${localStorage.getItem('token')}`
                }
            });
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
        { name: "Batalha de Ações (Comparador)", free: true, premium: true },
        { name: "Scores Avançados (Qualidade)", free: false, premium: true },
        { name: "Relatórios PDF Completos", free: false, premium: true },
        { name: "Recomendação IA (Buy/Hold/Sell)", free: false, premium: true },
        { name: "Calendário de Dividendos", free: false, premium: true },
        { name: "Sem Anúncios / Foco Total", free: false, premium: true },
        { name: "Suporte Prioritário", free: false, premium: true },
    ];

    const faqs = [
        { q: "O pagamento é seguro?", a: "Sim! Usamos o Stripe, a mesma plataforma de pagamentos da Amazon e Google. Seus dados nunca passam pelos nossos servidores." },
        { q: "Posso cancelar quando quiser?", a: "Com certeza. Sem letras miúdas. Você cancela com 1 clique no seu perfil e o acesso continua até o fim do mês pago." },
        { q: "Tenho garantia?", a: "Sim. Se você não gostar nos primeiros 7 dias, devolvemos 100% do seu dinheiro. Sem perguntas." },
    ];

    return (
        <div className="min-h-screen bg-[#0B0C15] text-white selection:bg-purple-500/30">
            {/* Background Glows */}
            <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-purple-600/20 rounded-full blur-[120px]" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[120px]" />
            </div>

            <div className="relative font-sans py-24 px-4 max-w-7xl mx-auto space-y-20">

                {/* Header */}
                <div className="text-center space-y-6 max-w-3xl mx-auto">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-sm font-medium text-purple-300"
                    >
                        <Star className="w-4 h-4 fill-purple-300" /> Nível Pro
                    </motion.div>

                    <motion.h1
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="text-5xl md:text-7xl font-bold tracking-tight bg-gradient-to-b from-white to-gray-400 bg-clip-text text-transparent"
                    >
                        Invista com a Inteligência dos Grandes
                    </motion.h1>

                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="text-xl text-gray-400"
                    >
                        Pare de adivinhar. Tenha acesso a relatórios profissionais, análise de IA e ferramentas exclusivas para multiplicar seu patrimônio.
                    </motion.p>
                </div>

                {/* Pricing Cards */}
                <div className="grid lg:grid-cols-2 gap-8 max-w-5xl mx-auto items-center">

                    {/* Basic Plan */}
                    <motion.div
                        initial={{ opacity: 0, x: -30 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.3 }}
                        className="p-8 rounded-3xl bg-white/5 border border-white/10 hover:bg-white/[0.07] transition-colors"
                    >
                        <div className="border-b border-white/10 pb-8 mb-8">
                            <h3 className="text-xl font-semibold text-gray-300">Iniciante</h3>
                            <div className="mt-4 flex items-baseline gap-1">
                                <span className="text-5xl font-bold text-white">R$ 0</span>
                                <span className="text-gray-500">/mês</span>
                            </div>
                            <p className="mt-2 text-sm text-gray-500">Para conhecer a plataforma.</p>

                            <button
                                disabled
                                className="mt-8 w-full py-4 rounded-xl font-semibold bg-white/10 text-gray-400 cursor-not-allowed border border-white/5"
                            >
                                Plano Atual
                            </button>
                        </div>

                        <ul className="space-y-4">
                            {features.map((feature, i) => (
                                <li key={i} className="flex items-center gap-3 text-sm">
                                    {feature.free ? (
                                        <Check className="w-5 h-5 text-gray-400 shrink-0" />
                                    ) : (
                                        <X className="w-5 h-5 text-gray-700 shrink-0" />
                                    )}
                                    <span className={feature.free ? 'text-gray-300' : 'text-gray-600'}>
                                        {feature.name}
                                    </span>
                                </li>
                            ))}
                        </ul>
                    </motion.div>

                    {/* Pro Plan */}
                    <motion.div
                        initial={{ opacity: 0, x: 30 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.4 }}
                        className="relative p-1 rounded-3xl bg-gradient-to-b from-purple-500 to-indigo-600 shadow-2xl shadow-purple-900/40"
                    >
                        <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-gradient-to-r from-amber-400 to-orange-500 text-black font-bold px-4 py-1 rounded-full text-xs uppercase tracking-wide shadow-lg flex items-center gap-1">
                            <Crown className="w-3 h-3 fill-black" /> Recomendado
                        </div>

                        <div className="bg-[#0B0C15] p-8 rounded-[22px] h-full flex flex-col relative overflow-hidden">
                            {/* Background Shine */}
                            <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />

                            <div className="border-b border-white/10 pb-8 mb-8 relative">
                                <h3 className="text-xl font-semibold text-purple-400 flex items-center gap-2">
                                    <Zap className="w-5 h-5" /> Investidor Pro
                                </h3>
                                <div className="mt-4 flex items-baseline gap-1">
                                    <span className="text-5xl font-bold text-white">R$ 29,90</span>
                                    <span className="text-gray-500">/mês</span>
                                </div>
                                <p className="mt-2 text-sm text-gray-400">Menos de R$ 1 por dia.</p>

                                <button
                                    onClick={handleSubscribe}
                                    disabled={isLoadingCheckout || user?.is_premium}
                                    className={`mt-8 w-full py-4 rounded-xl font-bold text-lg transition-all transform hover:scale-[1.02] shadow-xl ${user?.is_premium
                                            ? 'bg-green-600 text-white cursor-default'
                                            : 'bg-white text-black hover:bg-gray-100 hover:shadow-white/10'
                                        }`}
                                >
                                    {isLoadingCheckout ? 'Processando...' : user?.is_premium ? 'Plano Ativo ✅' : 'Quero Ser Pro 🚀'}
                                </button>
                                <p className="mt-3 text-center text-xs text-gray-500 flex items-center justify-center gap-1">
                                    <Shield className="w-3 h-3" /> 7 dias de garantia incondicional
                                </p>
                            </div>

                            <ul className="space-y-4 relative">
                                {features.map((feature, i) => (
                                    <li key={i} className="flex items-center gap-3 text-sm">
                                        {feature.premium ? (
                                            <div className="p-1 rounded-full bg-purple-500/20">
                                                <Check className="w-4 h-4 text-purple-400 shrink-0" />
                                            </div>
                                        ) : (
                                            <X className="w-5 h-5 text-gray-600 shrink-0" />
                                        )}
                                        <span className={feature.premium ? 'text-white font-medium' : 'text-gray-500'}>
                                            {feature.name}
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </motion.div>
                </div>

                {/* FAQ Section */}
                <div className="max-w-2xl mx-auto pt-10 border-t border-white/10">
                    <h2 className="text-2xl font-bold text-center mb-8">Perguntas Frequentes</h2>
                    <div className="space-y-4">
                        {faqs.map((faq, i) => (
                            <div key={i} className="bg-white/5 rounded-xl border border-white/5 overflow-hidden">
                                <button
                                    onClick={() => setOpenFaq(openFaq === i ? null : i)}
                                    className="w-full flex items-center justify-between p-4 text-left hover:bg-white/5 transition-colors"
                                >
                                    <span className="font-medium text-gray-300">{faq.q}</span>
                                    <ChevronDown className={`w-5 h-5 text-gray-500 transition-transform ${openFaq === i ? 'rotate-180' : ''}`} />
                                </button>
                                {openFaq === i && (
                                    <div className="p-4 pt-0 text-gray-400 text-sm leading-relaxed border-t border-white/5 bg-black/20">
                                        <HelpCircle className="w-4 h-4 inline-block mr-2 text-purple-400" />
                                        {faq.a}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

            </div>
        </div>
    );
}
