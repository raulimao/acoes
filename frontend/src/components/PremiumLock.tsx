'use client';
import React from 'react';
import { Lock, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';

interface PremiumLockProps {
    title?: string;
    description?: string;
}

export default function PremiumLock({
    title = "⛔ Acesso Restrito a Investidores Pro",
    description = "Existem 97 Oportunidades acima da média escondidas aqui."
}: PremiumLockProps) {
    const router = useRouter();

    return (
        <div className="absolute inset-0 backdrop-blur-sm bg-slate-950/60 flex flex-col items-center justify-center text-center p-6 z-20 rounded-xl border border-white/5">
            <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.3 }}
                className="bg-gradient-to-br from-slate-900 to-slate-800 p-6 rounded-2xl border border-white/10 shadow-2xl max-w-sm w-full"
            >
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-red-500 to-pink-600 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-red-500/20">
                    <Lock className="w-6 h-6 text-white" />
                </div>

                <h3 className="text-xl font-bold text-white mb-2 leading-tight">
                    {title}
                </h3>

                <div className="text-slate-400 mb-6 text-sm space-y-2">
                    <p>{description}</p>
                    <p className="text-yellow-400 font-semibold">
                        📉 Não invista no escuro.
                    </p>
                    <p className="text-xs text-white/50">
                        Você está deixando de ver ações com potencial de valorização 3x maior que a Poupança.
                    </p>
                </div>

                <button
                    className="w-full py-3 px-4 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold rounded-xl transition-all shadow-lg shadow-cyan-500/20 flex items-center justify-center gap-2 group"
                    onClick={() => router.push('/pricing')}
                >
                    <span>Ver Ranking Completo</span>
                    <Sparkles className="w-4 h-4 group-hover:rotate-12 transition-transform" />
                </button>

                <p className="mt-4 text-xs text-slate-500">
                    Risco Zero. Cancele quando quiser.
                </p>
            </motion.div>
        </div>
    );
}
