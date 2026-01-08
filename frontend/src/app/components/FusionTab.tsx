'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
    Target,
    TrendingUp,
    TrendingDown,
    Minus,
    ChevronRight,
    RefreshCcw,
    Crown,
    BarChart3,
    Zap
} from 'lucide-react';
import StatCard from './StatCard';
import StockDetailModal from './StockDetailModal';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

interface FusionStock {
    ticker: string;
    company_name: string;
    sector: string;
    price: number;
    fund_score_raw: number;
    tech_prob: number;
    fusion_score: number;
    matches_tech: boolean;
    tv_signal?: string;
    rsi?: number;
    ema200?: number;
    timing_signal?: string;
    timing_emoji?: string;
    // AI Verdict fields
    ai_verdict?: string;
    ai_verdict_color?: string;
    ai_recommendation?: string;
    ai_fund_score?: number;
    ai_tech_score?: number;
}

// Helper: Get timing badge config
const getTimingConfig = (timing?: string) => {
    switch (timing) {
        case 'ÓTIMO':
            return {
                bg: 'bg-emerald-500/10',
                border: 'border-emerald-500/30',
                text: 'text-emerald-400',
                icon: TrendingUp,
                label: 'Ótimo'
            };
        case 'BARGANHA':
            return {
                bg: 'bg-amber-500/10',
                border: 'border-amber-500/30',
                text: 'text-amber-400',
                icon: TrendingUp,
                label: 'Barganha'
            };
        case 'ESTICADO':
            return {
                bg: 'bg-orange-500/10',
                border: 'border-orange-500/30',
                text: 'text-orange-400',
                icon: Minus,
                label: 'Esticado'
            };
        case 'PERIGO':
            return {
                bg: 'bg-red-500/10',
                border: 'border-red-500/30',
                text: 'text-red-400',
                icon: TrendingDown,
                label: 'Perigo'
            };
        default:
            return {
                bg: 'bg-slate-500/10',
                border: 'border-slate-500/30',
                text: 'text-slate-400',
                icon: Minus,
                label: 'Neutro'
            };
    }
};

// Helper: Get signal color
const getSignalColor = (signal?: string) => {
    if (signal?.includes('STRONG_BUY')) return 'text-emerald-400';
    if (signal?.includes('BUY')) return 'text-green-400';
    if (signal?.includes('STRONG_SELL')) return 'text-red-400';
    if (signal?.includes('SELL')) return 'text-orange-400';
    return 'text-slate-400';
};

// Helper: Get AI Verdict badge config
const getVerdictConfig = (color?: string) => {
    switch (color) {
        case 'emerald':
            return { bg: 'bg-emerald-500/20', border: 'border-emerald-500/40', text: 'text-emerald-400' };
        case 'green':
            return { bg: 'bg-green-500/20', border: 'border-green-500/40', text: 'text-green-400' };
        case 'cyan':
            return { bg: 'bg-cyan-500/20', border: 'border-cyan-500/40', text: 'text-cyan-400' };
        case 'amber':
            return { bg: 'bg-amber-500/20', border: 'border-amber-500/40', text: 'text-amber-400' };
        case 'red':
            return { bg: 'bg-red-500/20', border: 'border-red-500/40', text: 'text-red-400' };
        default:
            return { bg: 'bg-slate-500/20', border: 'border-slate-500/40', text: 'text-slate-400' };
    }
};

export default function FusionTab() {
    const [stocks, setStocks] = useState<FusionStock[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
    const [showModal, setShowModal] = useState(false);

    const handleStockClick = (ticker: string) => {
        setSelectedTicker(ticker);
        setShowModal(true);
    };

    const fetchFusion = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${API_URL}/fusion/ranking`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                setStocks(data);
            } else {
                setError('Falha ao carregar ranking.');
            }
        } catch (e) {
            console.error(e);
            setError('Erro de conexão.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchFusion();
    }, []);

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center py-24 gap-4">
                <div className="relative">
                    <div className="w-16 h-16 rounded-full border-4 border-slate-700 border-t-cyan-500 animate-spin" />
                    <Target className="w-6 h-6 text-cyan-400 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                </div>
                <p className="text-slate-400 text-sm">Analisando mercado...</p>
            </div>
        );
    }

    // Stats
    const topOpportunities = stocks.filter(s => s.matches_tech && s.fusion_score > 80).length;
    const avgScore = stocks.length > 0
        ? (stocks.reduce((acc, s) => acc + s.fusion_score, 0) / stocks.length).toFixed(1)
        : '0';

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="space-y-6"
        >
            {/* Minimal Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
                        <Target className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <h2 className="text-xl font-semibold text-white">Ação Perfeita</h2>
                        <p className="text-xs text-slate-500">Fundamentos + Análise Técnica</p>
                    </div>
                </div>
                <button
                    onClick={() => fetchFusion()}
                    className="p-2 hover:bg-slate-800 rounded-lg transition-colors group"
                >
                    <RefreshCcw className="w-4 h-4 text-slate-500 group-hover:text-cyan-400 transition-colors" />
                </button>
            </div>

            {/* Standardized Header Metrics Grid */}
            <div className="dashboard-stats-grid">
                <StatCard
                    title="Ativos Analisados"
                    value={stocks.length}
                    icon={BarChart3}
                    gradient="from-slate-700 to-slate-800"
                    tooltip="Quantidade total de ativos monitorados pelo algoritmo Fusion."
                />
                <StatCard
                    title="Oportunidades"
                    value={topOpportunities}
                    subtitle="Fusion > 80"
                    icon={Zap}
                    gradient="from-emerald-400 to-teal-600"
                    valueColor="text-emerald-400"
                    tooltip="Ativos que atendem simultaneamente aos critérios de Qualidade e Preço."
                />
                <StatCard
                    title="Score Médio"
                    value={avgScore}
                    icon={Target}
                    gradient="from-cyan-400 to-blue-600"
                    tooltip="Média do Algoritmo Fusion para todos os ativos no ranking atual."
                />
            </div>

            {/* Error */}
            {error && (
                <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm text-center">
                    {error}
                </div>
            )}

            {/* Stocks Table */}
            <div className="bg-slate-800/30 rounded-xl border border-slate-700/50 overflow-hidden">
                {/* Table Header */}
                <div className="hidden md:grid grid-cols-14 gap-2 px-4 py-3 bg-slate-800/60 border-b border-slate-700/50 text-xs font-medium text-slate-400 uppercase tracking-wider">
                    <div className="col-span-1 text-center">#</div>
                    <div className="col-span-2">Ativo</div>
                    <div className="col-span-2 text-center">AI Verdict</div>
                    <div className="col-span-1 text-center">Score</div>
                    <div className="col-span-2 text-center">Fundamentos</div>
                    <div className="col-span-1 text-center">Técnico</div>
                    <div className="col-span-1 text-center">RSI</div>
                    <div className="col-span-2 text-center">Timing</div>
                    <div className="col-span-2 text-right">Preço</div>
                </div>

                {/* Stocks List */}
                <div className="divide-y divide-slate-700/30">
                    {stocks.map((stock, index) => {
                        const timingConfig = getTimingConfig(stock.timing_signal);
                        const TimingIcon = timingConfig.icon;
                        const isTop3 = index < 3;
                        const isOpportunity = stock.matches_tech && stock.fusion_score > 80;

                        return (
                            <motion.div
                                key={stock.ticker}
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: index * 0.02 }}
                                onClick={() => handleStockClick(stock.ticker)}
                                className={`
                                    group relative grid grid-cols-14 gap-2 px-4 py-3 items-center
                                    transition-all duration-150 cursor-pointer
                                    ${isTop3
                                        ? 'bg-gradient-to-r from-cyan-500/5 to-transparent hover:from-cyan-500/10'
                                        : 'hover:bg-slate-700/20'
                                    }
                                `}
                            >
                                {/* Rank */}
                                <div className="col-span-1 flex justify-center">
                                    {isTop3 ? (
                                        <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold text-white shadow-sm ${index === 0 ? 'bg-gradient-to-br from-amber-400 to-orange-500' :
                                            index === 1 ? 'bg-gradient-to-br from-slate-300 to-slate-400' :
                                                'bg-gradient-to-br from-amber-600 to-amber-700'
                                            }`}>
                                            {index + 1}
                                        </div>
                                    ) : (
                                        <span className="text-sm font-mono text-slate-500">{index + 1}</span>
                                    )}
                                </div>

                                {/* Ticker & Company */}
                                <div className="col-span-2">
                                    <div className="flex items-center gap-1.5">
                                        <span className={`font-semibold ${isTop3 ? 'text-white' : 'text-slate-200'}`}>
                                            {stock.ticker}
                                        </span>
                                        {isOpportunity && (
                                            <Crown className="w-3 h-3 text-amber-400" />
                                        )}
                                    </div>
                                    <p className="text-[11px] font-medium text-slate-400 truncate max-w-[120px]" title={stock.company_name}>
                                        {stock.company_name}
                                    </p>
                                    <p className="text-[9px] text-slate-600 truncate">{stock.sector}</p>
                                </div>

                                {/* AI Verdict Badge */}
                                <div className="col-span-2 flex justify-center">
                                    {(() => {
                                        const vConfig = getVerdictConfig(stock.ai_verdict_color);
                                        return (
                                            <div className={`
                                                inline-flex items-center gap-1 px-2 py-1 rounded-md border text-xs font-semibold
                                                ${vConfig.bg} ${vConfig.border}
                                            `}>
                                                <span className={vConfig.text}>
                                                    {stock.ai_recommendation || stock.ai_verdict || '-'}
                                                </span>
                                            </div>
                                        );
                                    })()}
                                </div>

                                {/* Fusion Score */}
                                <div className="col-span-1 text-center hidden md:block">
                                    <span className={`text-base font-bold ${stock.fusion_score >= 90 ? 'text-cyan-400' : stock.fusion_score >= 80 ? 'text-white' : 'text-slate-300'}`}>
                                        {stock.fusion_score.toFixed(1)}
                                    </span>
                                </div>

                                {/* Fundamentals Bar - RESTORED */}
                                <div className="col-span-2 hidden md:flex items-center gap-2">
                                    <div className="flex-1 h-1.5 bg-slate-700/50 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-gradient-to-r from-green-500 to-emerald-400 rounded-full transition-all"
                                            style={{ width: `${Math.min((stock.fund_score_raw / 30) * 100, 100)}%` }}
                                        />
                                    </div>
                                    <span className="text-xs text-slate-400 w-8">{stock.fund_score_raw.toFixed(1)}</span>
                                </div>

                                {/* Technical Signal - RESTORED */}
                                <div className="col-span-1 text-center hidden md:block">
                                    <span className={`text-xs font-medium ${getSignalColor(stock.tv_signal)}`}>
                                        {stock.tv_signal?.replace('STRONG_', '').replace('_', ' ') || '-'}
                                    </span>
                                </div>

                                {/* RSI - RESTORED */}
                                <div className="col-span-1 text-center hidden md:block">
                                    <span className={`text-sm font-medium ${(stock.rsi ?? 50) > 70 ? 'text-orange-400' :
                                        (stock.rsi ?? 50) < 30 ? 'text-emerald-400' :
                                            'text-slate-300'
                                        }`}>
                                        {stock.rsi?.toFixed(0) ?? '-'}
                                    </span>
                                </div>

                                {/* Timing Badge */}
                                <div className="col-span-2 flex justify-center">
                                    <div className={`
                                        inline-flex items-center gap-1 px-2 py-1 rounded-md border text-xs
                                        ${timingConfig.bg} ${timingConfig.border}
                                    `}>
                                        <TimingIcon className={`w-3 h-3 ${timingConfig.text}`} />
                                        <span className={`font-medium ${timingConfig.text}`}>
                                            {timingConfig.label}
                                        </span>
                                    </div>
                                </div>

                                {/* Price */}
                                <div className="col-span-2 text-right flex items-center justify-end gap-2">
                                    <span className="text-sm font-medium text-white">R$ {stock.price.toFixed(2)}</span>
                                    <ChevronRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-slate-400 group-hover:translate-x-0.5 transition-all" />
                                </div>

                                {/* Mobile: Compact Row */}
                                <div className="col-span-14 md:hidden flex items-center justify-between mt-2 pt-2 border-t border-slate-700/30">
                                    <div className="flex items-center gap-4">
                                        <div>
                                            <span className="text-base font-bold text-cyan-400">{stock.fusion_score.toFixed(1)}</span>
                                            <span className="text-[10px] text-slate-500 ml-1">score</span>
                                        </div>
                                        <span className={`text-xs ${getSignalColor(stock.tv_signal)}`}>
                                            {stock.tv_signal?.replace('STRONG_', '') || '-'}
                                        </span>
                                        <span className="text-xs text-slate-400">RSI {stock.rsi?.toFixed(0) ?? '-'}</span>
                                    </div>
                                </div>
                            </motion.div>
                        );
                    })}
                </div>
            </div>

            {/* Footer Legend */}
            <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 pt-4 text-xs text-slate-500">
                <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-emerald-400" />
                    <span>Ótimo</span>
                </div>
                <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-amber-400" />
                    <span>Barganha</span>
                </div>
                <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-orange-400" />
                    <span>Esticado</span>
                </div>
                <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-red-400" />
                    <span>Perigo</span>
                </div>
                <span className="text-slate-600">|</span>
                <span>Score = 70% Fundamentos + 30% Técnico</span>
            </div>

            {/* Stock Detail Modal */}
            {selectedTicker && (
                <StockDetailModal
                    ticker={selectedTicker}
                    isOpen={showModal}
                    onClose={() => setShowModal(false)}
                />
            )}
        </motion.div>
    );
}
