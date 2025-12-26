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
        <div className="min-h-screen bg-[#0B0C15] text-white selection:bg-purple-500/30 overflow-x-hidden">
            {/* Background Glows (Fixed opacity and size) */}
            <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
                <div className="absolute top-[-10%] left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-purple-600/10 rounded-full blur-[100px]" />
                <div className="absolute bottom-[-10%] left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-blue-600/5 rounded-full blur-[100px]" />
            </div>

            <div className="relative font-sans py-12 md:py-24 px-4 max-w-6xl mx-auto space-y-16 z-10">

                {/* Header */}
                <div className="text-center space-y-6 max-w-4xl mx-auto">
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-sm font-medium text-purple-300 backdrop-blur-md"
                    >
                        <Star className="w-4 h-4 fill-purple-300" /> <span>Nível Profissional</span>
                    </motion.div>

                    <motion.h1
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="text-4xl md:text-6xl font-bold tracking-tight bg-gradient-to-b from-white to-gray-400 bg-clip-text text-transparent leading-[1.1]"
                    >
                        Invista com a<br className="hidden md:block" /> Inteligência dos Grandes
                    </motion.h1>

                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto"
                    >
                        Pare de adivinhar. Tenha acesso a relatórios profissionais, análise de IA e ferramentas exclusivas.
                    </motion.p>
                </div>

                {/* Pricing Cards */}
                <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto items-stretch">

                    {/* Basic Plan */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                        className="flex flex-col p-8 rounded-3xl bg-white/5 border border-white/10 hover:bg-white/[0.07] transition-colors"
                    >
                        <div className="border-b border-white/10 pb-6 mb-6">
                            <h3 className="text-xl font-semibold text-gray-300">Iniciante</h3>
                            <div className="mt-4 flex items-baseline gap-1">
                                <span className="text-4xl font-bold text-white">R$ 0</span>
                                <span className="text-gray-500">/mês</span>
                            </div>
                            <p className="mt-2 text-sm text-gray-500">Para conhecer a plataforma.</p>

                            <button
                                disabled
                                className="mt-6 w-full py-3 rounded-xl font-semibold bg-white/5 text-gray-500 cursor-not-allowed border border-white/5"
                            >
                                Plano Atual
                            </button>
                        </div>

                        <ul className="space-y-4 flex-1">
                            {features.map((feature, i) => (
                                <li key={i} className="flex items-start gap-3 text-sm">
                                    {feature.free ? (
                                        <Check className="w-5 h-5 text-gray-400 shrink-0 mt-0.5" />
                                    ) : (
                                        <X className="w-5 h-5 text-gray-800 shrink-0 mt-0.5" />
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
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 }}
                        className="relative p-[2px] rounded-3xl bg-gradient-to-b from-purple-500 via-indigo-500 to-blue-600 shadow-2xl shadow-purple-900/30 lg:-mt-8 lg:mb-4 transform hover:-translate-y-1 transition-transform duration-300"
                    >
                        <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-gradient-to-r from-amber-400 to-orange-500 text-black font-bold px-4 py-1.5 rounded-full text-xs uppercase tracking-wide shadow-lg flex items-center gap-1 z-20 whitespace-nowrap">
                            <Crown className="w-3.5 h-3.5 fill-black" /> Recomendado
                        </div>

                        <div className="bg-[#0B0C15] p-8 rounded-[22px] h-full flex flex-col relative overflow-hidden">
                            {/* Background Shine */}
                            <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none" />

                            <div className="border-b border-white/10 pb-6 mb-6 relative z-10">
                                <h3 className="text-xl font-semibold text-purple-400 flex items-center gap-2">
                                    <Zap className="w-5 h-5 fill-purple-400" /> Investidor Pro
                                </h3>
                                <div className="mt-4 flex items-baseline gap-1">
                                    <span className="text-5xl font-bold text-white">R$ 29,90</span>
                                    <span className="text-gray-500">/mês</span>
                                </div>
                                <p className="mt-2 text-sm text-gray-400">Menos de R$ 1 por dia. Cancele quando quiser.</p>

                                <button
                                    onClick={handleSubscribe}
                                    disabled={isLoadingCheckout || user?.is_premium}
                                    className={`mt-6 w-full py-4 rounded-xl font-bold text-lg transition-all shadow-lg ${user?.is_premium
                                            ? 'bg-green-600 text-white cursor-default'
                                            : 'bg-white text-black hover:bg-gray-200 hover:shadow-white/20 active:scale-95'
                                        }`}
                                >
                                    {isLoadingCheckout ? 'Processando...' : user?.is_premium ? 'Plano Ativo ✅' : 'Quero Ser Pro 🚀'}
                                </button>

                                <div className="mt-3 flex items-center justify-center gap-2 text-xs text-gray-500">
                                    <Shield className="w-3 h-3" /> Garantia de 7 dias
                                </div>
                            </div>

                            <ul className="space-y-4 relative z-10 flex-1">
                                {features.map((feature, i) => (
                                    <li key={i} className="flex items-start gap-3 text-sm">
                                        {feature.premium ? (
                                            <div className="mt-0.5 p-0.5 rounded-full bg-purple-500/20 shrink-0">
                                                <Check className="w-3.5 h-3.5 text-purple-400" />
                                            </div>
                                        ) : (
                                            <X className="w-5 h-5 text-gray-600 shrink-0 mt-0.5" />
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
                <div className="max-w-3xl mx-auto pt-10 border-t border-white/10">
                    <h2 className="text-2xl font-bold text-center mb-8">Dúvidas Comuns</h2>
                    <div className="space-y-3">
                        {faqs.map((faq, i) => (
                            <div key={i} className="bg-white/5 rounded-xl border border-white/5 overflow-hidden transition-all hover:bg-white/[0.07]">
                                <button
                                    onClick={() => setOpenFaq(openFaq === i ? null : i)}
                                    className="w-full flex items-center justify-between p-4 text-left"
                                >
                                    <span className="font-medium text-gray-200 pr-4">{faq.q}</span>
                                    <ChevronDown className={`w-5 h-5 text-gray-500 transition-transform duration-200 ${openFaq === i ? 'rotate-180' : ''}`} />
                                </button>
                                {openFaq === i && (
                                    <div className="px-4 pb-4 text-gray-400 text-sm leading-relaxed animate-in slide-in-from-top-2 fade-in duration-200">
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
