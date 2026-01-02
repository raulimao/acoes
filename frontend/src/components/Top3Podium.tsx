'use client';

import { motion } from 'framer-motion';
import { Trophy, Zap, TrendingUp, Target, Star, Crown, Medal, Award } from 'lucide-react';

interface Stock {
    papel: string;
    setor?: string;
    cotacao?: number;
    p_l?: number;
    p_vp?: number;
    dividend_yield?: number;
    roe?: number;
    roic?: number;
    score_graham?: number;
    score_greenblatt?: number;
    score_bazin?: number;
    score_qualidade?: number;
    super_score?: number;
}

interface Top3PodiumProps {
    stocks: Stock[];
    onSelectStock: (stock: Stock) => void;
}

export default function Top3Podium({ stocks, onSelectStock }: Top3PodiumProps) {
    const top3 = stocks.slice(0, 3);

    if (top3.length === 0) return null;

    // Reorder for podium: 2nd, 1st, 3rd
    const podiumOrder = top3.length >= 3
        ? [top3[1], top3[0], top3[2]]
        : top3;

    const getPlacement = (index: number) => {
        if (top3.length < 3) return index;
        return index === 0 ? 1 : index === 1 ? 0 : 2;
    };

    const getMedalConfig = (place: number) => {
        switch (place) {
            case 0: return {
                icon: Crown,
                label: 'Campeão',
                gradient: 'from-yellow-400 via-yellow-500 to-amber-600',
                borderColor: 'border-yellow-500/50',
                bgGlow: 'shadow-yellow-500/20',
                textColor: 'text-yellow-400',
                height: 'h-[420px]',
                badgeBg: 'bg-gradient-to-r from-yellow-400 to-amber-500'
            };
            case 1: return {
                icon: Medal,
                label: 'Vice',
                gradient: 'from-gray-300 via-gray-400 to-gray-500',
                borderColor: 'border-gray-400/50',
                bgGlow: 'shadow-gray-400/20',
                textColor: 'text-gray-300',
                height: 'h-[380px]',
                badgeBg: 'bg-gradient-to-r from-gray-300 to-gray-400'
            };
            case 2: return {
                icon: Award,
                label: 'Bronze',
                gradient: 'from-orange-400 via-orange-500 to-orange-600',
                borderColor: 'border-orange-500/50',
                bgGlow: 'shadow-orange-500/20',
                textColor: 'text-orange-400',
                height: 'h-[360px]',
                badgeBg: 'bg-gradient-to-r from-orange-400 to-orange-600'
            };
            default: return {
                icon: Star,
                label: '',
                gradient: 'from-gray-500 to-gray-600',
                borderColor: 'border-gray-500/50',
                bgGlow: '',
                textColor: 'text-gray-400',
                height: 'h-[340px]',
                badgeBg: 'bg-gray-500'
            };
        }
    };

    const generateInsight = (stock: Stock): string => {
        const insights = [];

        if (stock.p_l && stock.p_l > 0 && stock.p_l < 10) {
            insights.push(`P/L de ${stock.p_l.toFixed(1)}x (muito barato)`);
        }
        if (stock.dividend_yield && stock.dividend_yield > 8) {
            insights.push(`DY de ${stock.dividend_yield.toFixed(1)}% (alto)`);
        }
        if (stock.roe && stock.roe > 20) {
            insights.push(`ROE de ${stock.roe.toFixed(0)}% (excelente)`);
        }
        if (stock.score_graham && stock.score_graham >= 4) {
            insights.push('Aprovado por Graham');
        }
        if (stock.score_qualidade && stock.score_qualidade >= 6) {
            insights.push('Alta Qualidade');
        }

        if (insights.length === 0) {
            insights.push('Equilíbrio entre indicadores');
        }

        return insights[0];
    };



    return (
        <div className="mb-8">
            {/* Header */}
            <div className="text-center mb-8">
                <motion.div
                    initial={{ scale: 0, rotate: -180 }}
                    animate={{ scale: 1, rotate: 0 }}
                    transition={{ type: 'spring', stiffness: 200 }}
                    className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-yellow-400 to-amber-600 mb-4 shadow-lg shadow-yellow-500/30"
                >
                    <Trophy className="w-8 h-8 text-white" />
                </motion.div>
                <h2 className="text-2xl font-bold text-white mb-2">Top 3 Ações da Semana</h2>
                <p className="text-white/50">Melhores oportunidades baseadas no Super Score</p>
            </div>

            {/* Podium */}
            <div className="flex flex-col md:flex-row items-end justify-center gap-4 max-w-4xl mx-auto px-4">
                {podiumOrder.map((stock, displayIndex) => {
                    const place = getPlacement(displayIndex);
                    const config = getMedalConfig(place);
                    const MedalIcon = config.icon;

                    return (
                        <motion.div
                            key={stock.papel}
                            className="w-full md:w-[280px] flex-shrink-0"
                            initial={{ opacity: 0, y: 50 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: displayIndex * 0.15, type: 'spring' }}
                        >
                            <div
                                className={`relative rounded-2xl border-2 ${config.borderColor} bg-gradient-to-b from-slate-800/80 to-slate-900/90 backdrop-blur-sm overflow-hidden cursor-pointer group transition-all duration-300 hover:scale-[1.02] ${config.bgGlow} shadow-xl ${config.height}`}
                                onClick={() => onSelectStock(stock)}
                            >
                                {/* Top Gradient Bar */}
                                <div className={`h-1.5 bg-gradient-to-r ${config.gradient}`} />

                                {/* Medal Badge */}
                                <div className="absolute -top-1 left-1/2 -translate-x-1/2">
                                    <div className={`${config.badgeBg} text-black px-4 py-1 rounded-b-xl font-bold text-sm flex items-center gap-1`}>
                                        <MedalIcon className="w-4 h-4" />
                                        {place + 1}º {config.label}
                                    </div>
                                </div>

                                {/* Content */}
                                <div className="p-6 pt-10 h-full flex flex-col">
                                    {/* Ticker & Sector */}
                                    <div className="text-center mb-4">
                                        <h3 className={`text-3xl font-black ${config.textColor} mb-1`}>
                                            {stock.papel}
                                        </h3>
                                        <p className="text-white/50 text-sm">{stock.setor || 'Sem setor'}</p>
                                    </div>

                                    {/* Super Score */}
                                    <div className="text-center mb-4">
                                        <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r ${config.gradient} text-black font-bold`}>
                                            <Zap className="w-4 h-4" />
                                            <span className="text-xl">{stock.super_score?.toFixed(1)}</span>
                                        </div>
                                        <p className="text-white/40 text-xs mt-1">Super Score</p>
                                    </div>

                                    {/* Insight */}
                                    <div className="text-center mb-4 px-2">
                                        <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10`}>
                                            <TrendingUp className={`w-4 h-4 ${config.textColor}`} />
                                            <span className="text-sm text-white/80">{generateInsight(stock)}</span>
                                        </div>
                                    </div>

                                    {/* Key Metrics */}
                                    <div className="grid grid-cols-2 gap-3 mb-4">
                                        <div className="bg-white/5 rounded-lg p-2 text-center">
                                            <p className="text-white/40 text-xs">Cotação</p>
                                            <p className="text-white font-bold">R$ {stock.cotacao?.toFixed(2)}</p>
                                        </div>
                                        <div className="bg-white/5 rounded-lg p-2 text-center">
                                            <p className="text-white/40 text-xs">P/L</p>
                                            <p className="text-white font-bold">{stock.p_l?.toFixed(1)}x</p>
                                        </div>
                                        <div className="bg-white/5 rounded-lg p-2 text-center">
                                            <p className="text-white/40 text-xs">DY</p>
                                            <p className="text-green-400 font-bold">{stock.dividend_yield?.toFixed(1)}%</p>
                                        </div>
                                        <div className="bg-white/5 rounded-lg p-2 text-center">
                                            <p className="text-white/40 text-xs">ROE</p>
                                            <p className="text-cyan-400 font-bold">{stock.roe?.toFixed(1)}%</p>
                                        </div>
                                    </div>

                                    {/* Strategy Scores */}
                                    <div className="mt-auto space-y-2">
                                        <p className="text-xs text-white/40 mb-2">Scores por Estratégia</p>
                                        <ScoreBar label="Graham" value={stock.score_graham || 0} max={5} color="bg-blue-500" />
                                        <ScoreBar label="Greenblatt" value={stock.score_greenblatt || 0} max={5} color="bg-purple-500" />
                                        <ScoreBar label="Bazin" value={stock.score_bazin || 0} max={5} color="bg-green-500" />
                                        <ScoreBar label="Qualidade" value={stock.score_qualidade || 0} max={7} color="bg-yellow-500" />
                                    </div>

                                    {/* CTA */}
                                    <motion.div
                                        className="mt-4 text-center opacity-0 group-hover:opacity-100 transition-opacity"
                                    >
                                        <span className="text-xs text-cyan-400">Clique para ver detalhes →</span>
                                    </motion.div>
                                </div>
                            </div>
                        </motion.div>
                    );
                })}
            </div>

            {/* Why Top 3 explanation */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="mt-8 text-center"
            >
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20">
                    <Target className="w-4 h-4 text-cyan-400" />
                    <span className="text-sm text-white/70">
                        Ranking baseado em <span className="text-cyan-400 font-medium">Graham</span>,
                        <span className="text-purple-400 font-medium"> Greenblatt</span>,
                        <span className="text-green-400 font-medium"> Bazin</span> e
                        <span className="text-yellow-400 font-medium"> Qualidade</span>
                    </span>
                </div>
            </motion.div>
        </div>
    );
}

const ScoreBar = ({ label, value, max, color }: { label: string; value: number; max: number; color: string }) => (
    <div className="space-y-1">
        <div className="flex justify-between text-xs">
            <span className="text-white/50">{label}</span>
            <span className="text-white/70 font-medium">{value.toFixed(1)}</span>
        </div>
        <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
            <motion.div
                className={`h-full rounded-full ${color}`}
                initial={{ width: 0 }}
                animate={{ width: `${(value / max) * 100}%` }}
                transition={{ duration: 0.8, delay: 0.3 }}
            />
        </div>
    </div>
);
