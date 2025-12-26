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
        <div className="min-h-screen bg-[#0B0C15] text-white selection:bg-purple-500/30 overflow-x-hidden flex flex-col items-center">

            {/* Background Glows */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
                <div className="absolute top-[-10%] left-1/2 -translate-x-1/2 w-[1000px] h-[1000px] bg-purple-600/10 rounded-full blur-[120px]" />
                <div className="absolute top-[20%] left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-blue-600/5 rounded-full blur-[100px]" />
            </div>

            <div className="relative font-sans w-full max-w-[1400px] mx-auto px-6 py-20 md:py-32 z-10 flex flex-col items-center gap-20">

                {/* Header Section */}
                <div className="text-center space-y-8 max-w-4xl mx-auto flex flex-col items-center">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-gradient-to-r from-purple-500/10 to-blue-500/10 border border-purple-500/20 text-sm font-semibold text-purple-300 backdrop-blur-md shadow-lg shadow-purple-900/10"
                    >
                        <Star className="w-4 h-4 fill-purple-300 text-purple-300" />
                        <span className="tracking-wide uppercase text-xs font-bold">Acesso Premium Disponível</span>
                    </motion.div>

                    <motion.h1
                        initial={{ opacity: 0, y: 30 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="text-5xl md:text-7xl lg:text-8xl font-black tracking-tight text-center leading-[1] md:leading-[1.1]"
                    >
                        <span className="bg-gradient-to-b from-white via-gray-100 to-gray-500 bg-clip-text text-transparent">Investimentos de</span><br />
                        <span className="bg-gradient-to-r from-purple-400 via-pink-400 to-amber-300 bg-clip-text text-transparent filter drop-shadow-2xl">Elite Mundial</span>
                    </motion.h1>

                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="text-xl md:text-2xl text-gray-400 max-w-3xl text-center leading-relaxed font-light"
                    >
                        Ferramentas profissionais de <strong>Graham & Bazin</strong>, IA preditiva e dados da B3 para quem joga para ganhar.
                    </motion.p>
                </div>

                {/* Social Proof */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3 }}
                    className="flex flex-wrap justify-center gap-8 md:gap-16 opacity-60 hover:opacity-100 transition-all duration-500"
                >
                    <div className="text-sm md:text-base font-bold text-gray-400 flex items-center gap-3"><Shield className="w-5 h-5" /> DADOS DA B3</div>
                    <div className="text-sm md:text-base font-bold text-gray-400 flex items-center gap-3"><Shield className="w-5 h-5" /> FUNDAMENTUS API</div>
                    <div className="text-sm md:text-base font-bold text-gray-400 flex items-center gap-3"><Shield className="w-5 h-5" /> INTEGRAÇÃO IA</div>
                </motion.div>

                {/* Pricing Cards Container - FLEX Layout for Safety */}
                <div className="flex flex-wrap justify-center gap-8 w-full items-start">

                    {/* Basic Plan */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 }}
                        className="w-full lg:w-[480px] bg-[#12131e]/80 backdrop-blur-md rounded-[32px] border border-white/5 p-8 md:p-10 flex flex-col hover:bg-[#151625] transition-colors duration-300 relative"
                    >
                        <div className="mb-6">
                            <h3 className="text-2xl font-bold text-gray-300 mb-2">Iniciante</h3>
                            <div className="flex items-baseline gap-2">
                                <span className="text-4xl font-bold text-white tracking-tight">R$ 0</span>
                                <span className="text-gray-500 text-lg font-medium">/mês</span>
                            </div>
                        </div>

                        <p className="text-gray-400 text-base leading-relaxed mb-8 min-h-[50px]">
                            Funcionalidades essenciais para quem está começando a organizar a carteira.
                        </p>

                        <button
                            disabled
                            className="w-full py-4 rounded-xl font-bold bg-white/5 text-gray-500 border border-white/5 uppercase text-xs tracking-widest cursor-not-allowed mb-8"
                        >
                            Seu Plano Atual
                        </button>

                        <div className="space-y-4 flex-1">
                            <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">O que está incluso</p>
                            {features.map((feature, i) => (
                                <div key={i} className="flex items-start gap-3 group">
                                    {feature.free ? (
                                        <div className="p-0.5 rounded-full bg-white/5 shrink-0 mt-0.5">
                                            <Check className="w-4 h-4 text-gray-300" />
                                        </div>
                                    ) : (
                                        <div className="p-0.5 shrink-0 mt-0.5 opacity-30">
                                            <X className="w-4 h-4 text-gray-500" />
                                        </div>
                                    )}
                                    <span className={`${feature.free ? 'text-gray-300' : 'text-gray-600 decoration-gray-700/50'} text-sm leading-snug`}>
                                        {feature.name}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </motion.div>

                    {/* Pro Plan - Highlights */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.5 }}
                        className="w-full lg:w-[500px] relative group"
                    >
                        {/* Glowing Border Effect */}
                        <div className="absolute -inset-[3px] bg-gradient-to-tr from-purple-600 via-pink-600 to-amber-400 rounded-[36px] blur-[20px] opacity-40 group-hover:opacity-80 transition duration-700 animate-pulse-slow"></div>

                        <div className="relative bg-[#161726] rounded-[32px] border border-white/10 p-8 md:p-10 overflow-hidden shadow-2xl shadow-purple-900/20">

                            {/* Recommended Badge - Positioned Safer */}
                            <div className="absolute top-6 right-6 z-20">
                                <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-gradient-to-r from-amber-400 to-orange-500 text-black text-[10px] font-black uppercase tracking-widest rounded-full shadow-lg shadow-amber-500/20 whitespace-nowrap">
                                    <Crown className="w-3 h-3 fill-black" /> Recomendado
                                </span>
                            </div>

                            <div className="mb-2 flex items-center gap-2">
                                <span className="p-1.5 rounded-lg bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/30">
                                    <Zap className="w-5 h-5 text-amber-400 fill-amber-400" />
                                </span>
                                <h3 className="text-2xl font-bold text-white">Investidor Pro</h3>
                            </div>

                            <div className="flex items-baseline gap-2 mb-6">
                                <span className="text-5xl font-black text-white tracking-tighter">R$ 29,90</span>
                                <span className="text-gray-400 text-lg font-medium">/mês</span>
                            </div>

                            <p className="text-purple-200/90 text-base leading-relaxed mb-8 min-h-[50px] pr-4">
                                A suíte completa para quem busca liberdade financeira real. Acesso ilimitado a todas as ferramentas.
                            </p>

                            <button
                                onClick={handleSubscribe}
                                disabled={isLoadingCheckout || user?.is_premium}
                                className={`w-full py-4 rounded-xl font-black text-sm uppercase tracking-widest transition-all transform hover:scale-[1.02] shadow-2xl mb-8 group/btn flex items-center justify-center gap-2 relative overflow-hidden ${user?.is_premium
                                        ? 'bg-green-600 text-white cursor-default'
                                        : 'bg-gradient-to-r from-purple-600 via-pink-600 to-amber-600 hover:from-purple-500 hover:to-amber-500 text-white shadow-purple-500/40'
                                    }`}
                            >
                                <span className="relative z-10">{isLoadingCheckout ? 'Processando...' : user?.is_premium ? 'Plano Ativo ✅' : 'Quero Ser Pro'}</span>
                                {(!isLoadingCheckout && !user?.is_premium) && <Crown className="w-4 h-4 relative z-10 mb-0.5" />}
                            </button>

                            <div className="space-y-4">
                                <p className="text-xs font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400 uppercase tracking-widest mb-3">Tudo do iniciante, mais:</p>
                                {features.map((feature, i) => (
                                    <div key={i} className="flex items-start gap-3">
                                        {feature.premium ? (
                                            <div className="p-0.5 rounded-full bg-green-500/10 shrink-0 mt-0.5 border border-green-500/20">
                                                <Check className="w-4 h-4 text-green-400 stroke-[3]" />
                                            </div>
                                        ) : (
                                            <div className="p-0.5 shrink-0 mt-0.5 opacity-30">
                                                <X className="w-4 h-4 text-gray-600" />
                                            </div>
                                        )}
                                        <span className={`${feature.premium ? 'text-white font-medium' : 'text-gray-600'} text-sm leading-snug`}>
                                            {feature.name}
                                        </span>
                                    </div>
                                ))}
                            </div>

                            <div className="mt-6 pt-4 border-t border-white/5 flex items-center justify-center gap-2 text-[10px] text-green-400/80 font-mono tracking-wide">
                                <Shield className="w-3 h-3" />
                                GARANTIA DE 7 DIAS
                            </div>
                        </div>
                    </motion.div>
                </div>

                {/* FAQ Section */}
                <div className="w-full max-w-4xl pt-20 border-t border-white/5">
                    <h2 className="text-3xl md:text-4xl font-bold text-center mb-16">
                        <span className="bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">Dúvidas Frequentes</span>
                    </h2>
                    <div className="grid gap-4">
                        {faqs.map((faq, i) => (
                            <div key={i} className="group bg-[#12131e] rounded-2xl border border-white/5 overflow-hidden transition-all duration-300 hover:border-purple-500/30">
                                <button
                                    onClick={() => setOpenFaq(openFaq === i ? null : i)}
                                    className="w-full flex items-center justify-between p-6 text-left"
                                >
                                    <span className="font-semibold text-gray-200 text-lg group-hover:text-purple-300 transition-colors">{faq.q}</span>
                                    <ChevronDown className={`w-6 h-6 text-gray-500 group-hover:text-purple-400 transition-transform duration-300 ${openFaq === i ? 'rotate-180' : ''}`} />
                                </button>
                                {openFaq === i && (
                                    <div className="px-6 pb-6 text-gray-400 text-base leading-relaxed animate-in slide-in-from-top-2 border-t border-white/5 pt-4">
                                        {faq.a}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Footer Brand */}
                <div className="pb-12 pt-12 text-center opacity-30">
                    <p className="text-sm tracking-[0.2em] uppercase font-bold text-gray-500">TopAções App © 2025</p>
                </div>

            </div>
        </div>
    );
}
