'use client';

import { motion } from 'framer-motion';
import { TrendingUp, Lock, Sparkles, ArrowRight } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface FOMOWidgetProps {
    isPremium: boolean;
    topStocks: Array<{ papel: string; super_score?: number; }>;
}

// Simulated data for FOMO - in production this would come from API tracking
const MISSED_OPPORTUNITIES = [
    { ticker: 'VALE3', gain: 15.2, days: 7 },
    { ticker: 'PETR4', gain: 8.7, days: 14 },
    { ticker: 'BBAS3', gain: 12.1, days: 7 },
];

export default function FOMOWidget({ isPremium, topStocks }: FOMOWidgetProps) {
    const router = useRouter();

    // Don't show for premium users
    if (isPremium) return null;

    const totalMissedGain = MISSED_OPPORTUNITIES.reduce((sum, opp) => sum + opp.gain, 0);

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 rounded-xl bg-gradient-to-r from-red-900/30 to-orange-900/30 border border-red-500/30 overflow-hidden"
        >
            {/* Header */}
            <div className="p-4 border-b border-red-500/20">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center animate-pulse">
                            <TrendingUp className="w-5 h-5 text-red-400" />
                        </div>
                        <div>
                            <h3 className="font-bold text-white">O que você está perdendo</h3>
                            <p className="text-sm text-white/50">Oportunidades da última semana</p>
                        </div>
                    </div>
                    <div className="text-right">
                        <p className="text-2xl font-bold text-red-400">+{totalMissedGain.toFixed(1)}%</p>
                        <p className="text-xs text-white/40">Ganho médio</p>
                    </div>
                </div>
            </div>

            {/* Opportunities List */}
            <div className="p-4 space-y-3">
                {MISSED_OPPORTUNITIES.map((opp, index) => (
                    <div
                        key={opp.ticker}
                        className="flex items-center justify-between p-3 rounded-lg bg-white/5"
                    >
                        <div className="flex items-center gap-3">
                            <span className="text-white/40 text-sm">#{index + 1}</span>
                            <div>
                                <p className="font-bold text-white">{opp.ticker}</p>
                                <p className="text-xs text-white/40">Últimos {opp.days} dias</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-green-400 font-bold">+{opp.gain}%</span>
                            <Lock className="w-4 h-4 text-yellow-400" />
                        </div>
                    </div>
                ))}
            </div>

            {/* CTA */}
            <div className="p-4 bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border-t border-yellow-500/20">
                <div className="flex items-center justify-between flex-wrap gap-3">
                    <div className="flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-yellow-400" />
                        <p className="text-sm text-white/80">
                            Não perca mais oportunidades como essas
                        </p>
                    </div>
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => router.push('/pricing')}
                        className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-yellow-400 to-orange-500 text-black font-bold rounded-lg text-sm"
                    >
                        Ver Oportunidades
                        <ArrowRight className="w-4 h-4" />
                    </motion.button>
                </div>
            </div>
        </motion.div>
    );
}
