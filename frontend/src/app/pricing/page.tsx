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
                <div className="absolute top-[-10%] left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-purple-600/10 rounded-full blur-[120px]" />
                <div className="absolute top-[20%] left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-blue-600/5 rounded-full blur-[100px]" />
            </div>

            <div className="relative font-sans w-full max-w-7xl mx-auto px-4 py-16 md:py-24 z-10 flex flex-col items-center gap-16">

                {/* Header Section */}
                <div className="text-center space-y-6 max-w-4xl mx-auto flex flex-col items-center">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-purple-500/10 to-blue-500/10 border border-purple-500/20 text-sm font-semibold text-purple-300 backdrop-blur-md shadow-lg shadow-purple-900/10"
                    >
                        <Star className="w-4 h-4 fill-purple-300 text-purple-300" />
                        <span className="tracking-wide uppercase text-xs">Acesso Premium Liberado</span>
                    </motion.div>

                    <motion.h1
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="text-4xl md:text-6xl lg:text-7xl font-black tracking-tight text-center leading-[1.1]"
                    >
                        <span className="bg-gradient-to-b from-white via-white to-gray-400 bg-clip-text text-transparent">Invista como</span><br />
                        <span className="bg-gradient-to-r from-purple-400 via-pink-400 to-amber-300 bg-clip-text text-transparent filter drop-shadow-2xl">um Gigante</span>
                    </motion.h1>

                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="text-lg md:text-xl text-gray-400 max-w-2xl text-center leading-relaxed"
                    >
                        Desbloqueie estratégias de <strong>Graham & Bazin</strong>, relatórios de IA e o poder dos dados para multiplicar seu patrimônio.
                    </motion.p>
                </div>

                {/* Social Proof */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3 }}
                    className="flex flex-wrap justify-center gap-6 md:gap-12 opacity-50 grayscale hover:grayscale-0 transition-all duration-500 mb-4"
                >
                    <div className="text-xs md:text-sm font-bold text-gray-400 flex items-center gap-2"><Shield className="w-4 h-4" /> DADOS DA B3</div>
                    <div className="text-xs md:text-sm font-bold text-gray-400 flex items-center gap-2"><Shield className="w-4 h-4" /> FUNDAMENTUS</div>
                    <div className="text-xs md:text-sm font-bold text-gray-400 flex items-center gap-2"><Shield className="w-4 h-4" /> INTEGRAÇÃO IA</div>
                </motion.div>

                {/* Pricing Cards Container */}
                <div className="grid md:grid-cols-2 gap-8 lg:gap-10 w-full max-w-5xl mx-auto items-stretch">

                    {/* Basic Plan */}
                    <motion.div
                        initial={{ opacity: 0, x: -30 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.4 }}
                        className="w-full flex flex-col p-10 rounded-[32px] bg-white/5 border border-white/5 hover:border-white/10 transition-colors backdrop-blur-sm"
                    >
                        {/* Header Box */}
                        <div className="border-b border-white/10 pb-8 mb-8 min-h-[160px] flex flex-col justify-between">
                            <div>
                                <h3 className="text-2xl font-semibold text-gray-400 mb-3">Iniciante</h3>
                                <div className="flex items-baseline gap-1">
                                    <span className="text-5xl font-bold text-white tracking-tight">R$ 0</span>
                                    <span className="text-gray-500 text-lg font-medium">/mês</span>
                                </div>
                                <p className="mt-3 text-sm text-gray-500 leading-relaxed pr-4">
                                    Acesso limitado para conhecer a plataforma e ferramentas básicas.
                                </p>
                            </div>
                        </div>

                        {/* Button Area */}
                        <div className="mb-8">
                            <button
                                disabled
                                className="w-full py-4 rounded-xl font-bold bg-white/5 text-gray-500 cursor-not-allowed border border-white/5 uppercase text-sm tracking-wide transition-colors hover:bg-white/10"
                            >
                                Seu Plano Atual
                            </button>
                        </div>

                        {/* Features List */}
                        <ul className="space-y-4 flex-1">
                            {features.map((feature, i) => (
                                <li key={i} className="flex items-start gap-4 text-sm group min-h-[24px]">
                                    {feature.free ? (
                                        <div className="mt-0.5 min-w-[20px]">
                                            <Check className="w-5 h-5 text-gray-500 shrink-0 group-hover:text-gray-300 transition-colors" />
                                        </div>
                                    ) : (
                                        <div className="mt-0.5 min-w-[20px]">
                                            <X className="w-5 h-5 text-gray-800 shrink-0" />
                                        </div>
                                    )}
                                    <span className={`${feature.free ? 'text-gray-300' : 'text-gray-600'} leading-tight`}>
                                        {feature.name}
                                    </span>
                                </li>
                            ))}
                        </ul>
                    </motion.div>

                    {/* Pro Plan - Highlights */}
                    <motion.div
                        initial={{ opacity: 0, x: 30 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.5 }}
                        className="w-full relative group flex flex-col"
                    >
                        {/* Glowing Border Effect */}
                        <div className="absolute -inset-[2px] bg-gradient-to-tr from-purple-600 via-pink-600 to-amber-500 rounded-[34px] blur-[12px] opacity-60 group-hover:opacity-100 transition duration-500 animate-pulse-slow"></div>

                        <div className="relative rounded-[32px] bg-[#13141f] h-full flex flex-col overflow-hidden border border-white/10 p-10">
                            {/* Top Gradient Line */}
                            <div className="absolute top-0 left-0 w-full bg-gradient-to-r from-purple-500 to-pink-500 h-1.5"></div>

                            {/* Recommended Badge */}
                            <div className="absolute top-6 right-6 z-20">
                                <span className="px-3 py-1.5 bg-gradient-to-r from-amber-400 to-orange-500 text-black text-[10px] md:text-xs font-black uppercase tracking-wider rounded-full shadow-lg shadow-amber-500/20 flex items-center gap-1">
                                    <Crown className="w-3.5 h-3.5 fill-black" /> Recomendado
                                </span>
                            </div>

                            {/* Header Box */}
                            <div className="border-b border-white/10 pb-8 mb-8 min-h-[160px] flex flex-col justify-between relative z-10">
                                <div>
                                    <h3 className="text-2xl font-bold text-white flex items-center gap-2 mb-3">
                                        <Zap className="w-6 h-6 text-amber-400 fill-amber-400" /> Investidor Pro
                                    </h3>
                                    <div className="flex items-baseline gap-1">
                                        <span className="text-5xl font-bold text-white tracking-tight">R$ 29,90</span>
                                        <span className="text-gray-400 text-lg font-medium">/mês</span>
                                    </div>
                                    <p className="mt-3 text-sm text-purple-200/80 leading-relaxed pr-4">
                                        Todas as ferramentas liberadas. Análise IA, Rankings e Carteiras recomendadas.
                                    </p>
                                </div>
                            </div>

                            {/* Button Area */}
                            <div className="mb-8 relative z-10">
                                <button
                                    onClick={handleSubscribe}
                                    disabled={isLoadingCheckout || user?.is_premium}
                                    className={`w-full py-4 rounded-xl font-black text-sm md:text-base uppercase tracking-wider transition-all transform hover:scale-[1.02] shadow-xl flex items-center justify-center gap-2 relative overflow-hidden group/btn ${user?.is_premium
                                        ? 'bg-green-600 text-white cursor-default'
                                        : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white shadow-purple-500/25'
                                        }`}
                                >
                                    <div className="absolute inset-0 bg-white/20 translate-y-full group-hover/btn:translate-y-0 transition-transform duration-300 skew-y-12"></div>
                                    <span className="relative z-10">{isLoadingCheckout ? 'Processando...' : user?.is_premium ? 'Plano Ativo ✅' : 'Quero Ser Pro'}</span>
                                    {(!isLoadingCheckout && !user?.is_premium) && <Crown className="w-4 h-4 mb-0.5 relative z-10" />}
                                </button>

                                <div className="mt-4 flex items-center justify-center gap-2 text-xs text-gray-400 font-medium">
                                    <Shield className="w-3.5 h-3.5 text-green-500" /> 7 dias de garantia ou reembolso
                                </div>
                            </div>

                            {/* Features List */}
                            <div className="flex-1 relative z-10">
                                <ul className="space-y-4">
                                    {features.map((feature, i) => (
                                        <li key={i} className="flex items-start gap-4 text-sm min-h-[24px]">
                                            {feature.premium ? (
                                                <div className="mt-0.5 min-w-[20px] rounded-full bg-green-500/10 flex items-center justify-center w-5 h-5">
                                                    <Check className="w-3.5 h-3.5 text-green-400 stroke-[3]" />
                                                </div>
                                            ) : (
                                                <div className="mt-0.5 min-w-[20px]">
                                                    <X className="w-5 h-5 text-gray-600 shrink-0" />
                                                </div>
                                            )}
                                            <span className={`${feature.premium ? 'text-white font-medium' : 'text-gray-500'} leading-tight`}>
                                                {feature.name}
                                            </span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    </motion.div>
                </div>

                {/* FAQ Section */}
                <div className="w-full max-w-3xl pt-16 border-t border-white/5">
                    <h2 className="text-2xl md:text-3xl font-bold text-center mb-10 bg-gradient-to-r from-gray-200 to-gray-400 bg-clip-text text-transparent">
                        Dúvidas Frequentes
                    </h2>
                    <div className="space-y-3">
                        {faqs.map((faq, i) => (
                            <div key={i} className="bg-white/[0.03] rounded-2xl border border-white/5 overflow-hidden hover:bg-white/[0.05] transition-colors">
                                <button
                                    onClick={() => setOpenFaq(openFaq === i ? null : i)}
                                    className="w-full flex items-center justify-between p-5 text-left"
                                >
                                    <span className="font-semibold text-gray-200 pr-8 text-sm md:text-base">{faq.q}</span>
                                    <ChevronDown className={`w-5 h-5 text-purple-400 transition-transform duration-300 ${openFaq === i ? 'rotate-180' : ''}`} />
                                </button>
                                {openFaq === i && (
                                    <div className="px-5 pb-5 text-gray-400 text-sm leading-relaxed animate-in slide-in-from-top-2">
                                        {faq.a}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Footer Brand */}
                <div className="pb-10 pt-10 text-center opacity-30">
                    <p className="text-xs md:text-sm tracking-widest uppercase font-bold text-gray-500">TopAções App © 2025</p>
                </div>

            </div>
        </div>
    );
}
