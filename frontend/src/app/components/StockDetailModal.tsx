'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronUp, ChevronDown, Rocket, AlertTriangle, Crosshair, TrendingUp, TrendingDown, Clock, Activity, DollarSign, Sparkles, X, Loader2, ExternalLink, CheckCircle } from 'lucide-react';
import { AdvancedRealTimeChart } from 'react-ts-tradingview-widgets';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

interface StockAnalysis {
    ticker: string;
    company_name?: string;
    sector: string;
    subsetor: string;
    price: number;
    change: number;
    volume: number;
    ai_verdict: {
        verdict: string;
        verdict_color: string;
        verdict_icon: string;
        recommendation: string;
        summary: string;
        fund_score: number;
        tech_score: number;
        total_score: number;
        highlights: string[];
        concerns: string[];
    };
    fair_value: {
        graham?: number;
        bazin?: number;
        earnings?: number;
        roe_based?: number;
        average?: number;
        upside?: number;
    };
    sector_ranking: {
        rank: number;
        total: number;
        percentile: number;
        top_3: Array<{ papel: string; super_score: number }>;
    };
    fundamental: {
        p_l: number;
        p_vp: number;
        dividend_yield: number;
        roe: number;
        roic: number;
        margem_liquida: number;
        liquidez_corrente: number;
        div_bruta_patrimonio: number;
        scores: {
            super_score: number;
            graham: number;
            greenblatt: number;
            bazin: number;
            qualidade: number;
        };
    };
    technical: {
        summary: string;
        summary_score: number;
        oscillators: { signal: string; buy: number; sell: number; neutral: number };
        moving_averages: { signal: string; buy: number; sell: number; neutral: number };
        indicators: {
            rsi: number | null;
            macd: { value: number; signal: number; histogram: number };
            stochastic: { k: number; d: number };
            adx: number;
            cci: number;
            bollinger: { upper: number; lower: number; middle: number; width: number };
            ema200: number | null;
            sma200: number;
            ema50: number;
            volume: number;
            change: number;
        };
        pivots: {
            classic: { s1: number; s2: number; s3: number; pivot: number; r1: number; r2: number; r3: number };
        };
        // New fields for the TradingView chart and indicators
        sma20?: number;
        sma50?: number;
    };
    timing: {
        signal: string;
        emoji: string;
        above_ema200: boolean | null;
        rsi_zone: string;
        distance_to_ema200: number | null;
    };
    analysis: { // Assuming 'analysis' is a new top-level field for distance_to_ema200
        distance_to_ema200?: number;
    }
}

interface Props {
    ticker: string;
    isOpen: boolean;
    onClose: () => void;
}

// Animated circular progress
const CircularProgress = ({ value, max, size = 80, color = 'cyan' }: { value: number; max: number; size?: number; color?: string }) => {
    const percentage = Math.min((value / max) * 100, 100);
    const strokeWidth = 6;
    const radius = (size - strokeWidth) / 2;
    const circumference = radius * 2 * Math.PI;
    const strokeDashoffset = circumference - (percentage / 100) * circumference;

    const colors: Record<string, string> = {
        cyan: '#06b6d4',
        green: '#10b981',
        amber: '#f59e0b',
        red: '#ef4444',
        purple: '#a855f7'
    };

    return (
        <div className="relative" style={{ width: size, height: size }}>
            <svg className="transform -rotate-90" width={size} height={size}>
                <circle
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    stroke="currentColor"
                    strokeWidth={strokeWidth}
                    fill="transparent"
                    className="text-slate-700"
                />
                <motion.circle
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    stroke={colors[color]}
                    strokeWidth={strokeWidth}
                    fill="transparent"
                    strokeLinecap="round"
                    initial={{ strokeDashoffset: circumference }}
                    animate={{ strokeDashoffset }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    style={{ strokeDasharray: circumference }}
                />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-lg font-bold text-white">{value.toFixed(1)}</span>
            </div>
        </div>
    );
};

// Premium RSI Gauge
const RSIGauge = ({ value }: { value: number | null }) => {
    if (value === null) return <div className="text-slate-500 text-center">N/A</div>;

    const rotation = ((value - 50) / 50) * 90; // -90 to +90 degrees
    const getColor = () => {
        if (value > 70) return { main: '#f97316', glow: 'rgba(249, 115, 22, 0.5)' };
        if (value < 30) return { main: '#10b981', glow: 'rgba(16, 185, 129, 0.5)' };
        return { main: '#06b6d4', glow: 'rgba(6, 182, 212, 0.5)' };
    };
    const colors = getColor();

    return (
        <div className="relative flex flex-col items-center">
            <div className="relative w-32 h-16 overflow-hidden">
                {/* Background arc */}
                <div className="absolute inset-0">
                    <svg viewBox="0 0 100 50" className="w-full h-full">
                        <defs>
                            <linearGradient id="rsiGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                <stop offset="0%" stopColor="#10b981" />
                                <stop offset="50%" stopColor="#06b6d4" />
                                <stop offset="100%" stopColor="#f97316" />
                            </linearGradient>
                        </defs>
                        <path
                            d="M 5 50 A 45 45 0 0 1 95 50"
                            fill="none"
                            stroke="url(#rsiGradient)"
                            strokeWidth="8"
                            strokeLinecap="round"
                            opacity="0.3"
                        />
                        {/* Active arc segments */}
                        <path
                            d="M 5 50 A 45 45 0 0 1 95 50"
                            fill="none"
                            stroke="url(#rsiGradient)"
                            strokeWidth="8"
                            strokeLinecap="round"
                            strokeDasharray="141.4"
                            strokeDashoffset={141.4 - (value / 100) * 141.4}
                        />
                    </svg>
                </div>
                {/* Needle */}
                <motion.div
                    className="absolute bottom-0 left-1/2 origin-bottom w-1 h-12 rounded-full"
                    style={{
                        background: `linear-gradient(to top, ${colors.main}, transparent)`,
                        boxShadow: `0 0 10px ${colors.glow}`
                    }}
                    initial={{ rotate: -90 }}
                    animate={{ rotate: rotation }}
                    transition={{ duration: 1, type: "spring", stiffness: 60 }}
                />
                {/* Center dot */}
                <div
                    className="absolute bottom-0 left-1/2 -translate-x-1/2 w-4 h-4 rounded-full border-2 border-white"
                    style={{ backgroundColor: colors.main, boxShadow: `0 0 15px ${colors.glow}` }}
                />
            </div>
            <motion.div
                className="mt-2 text-center"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
            >
                <span className="text-2xl font-bold" style={{ color: colors.main }}>{value.toFixed(0)}</span>
                <p className="text-[10px] text-slate-400 uppercase">
                    {value > 70 ? 'Sobrecomprado' : value < 30 ? 'Sobrevendido' : 'Neutro'}
                </p>
            </motion.div>
        </div>
    );
};

// Verdict color map
const verdictColors: Record<string, { bg: string; border: string; text: string; glow: string }> = {
    emerald: { bg: 'from-emerald-500/20 to-emerald-600/10', border: 'border-emerald-500/50', text: 'text-emerald-400', glow: 'shadow-emerald-500/20' },
    green: { bg: 'from-green-500/20 to-green-600/10', border: 'border-green-500/50', text: 'text-green-400', glow: 'shadow-green-500/20' },
    cyan: { bg: 'from-cyan-500/20 to-cyan-600/10', border: 'border-cyan-500/50', text: 'text-cyan-400', glow: 'shadow-cyan-500/20' },
    slate: { bg: 'from-slate-500/20 to-slate-600/10', border: 'border-slate-500/50', text: 'text-slate-400', glow: 'shadow-slate-500/20' },
    amber: { bg: 'from-amber-500/20 to-amber-600/10', border: 'border-amber-500/50', text: 'text-amber-400', glow: 'shadow-amber-500/20' },
    red: { bg: 'from-red-500/20 to-red-600/10', border: 'border-red-500/50', text: 'text-red-400', glow: 'shadow-red-500/20' }
};

export default function StockDetailModal({ ticker, isOpen, onClose }: Props) {
    const [data, setData] = useState<StockAnalysis | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'resumo' | 'fundamental' | 'tecnico'>('resumo');

    useEffect(() => {
        if (isOpen && ticker) {
            fetchData();
            setActiveTab('resumo');
        }
    }, [isOpen, ticker]);

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        setData(null);  // Clear stale data before fetching new
        try {
            const token = localStorage.getItem('token');
            const res = await fetch(`${API_URL}/stock/${ticker}/full-analysis`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!res.ok) throw new Error('Falha ao carregar dados');
            const json = await res.json();
            setData(json);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : 'Erro desconhecido');
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    const vColors = data?.ai_verdict ? verdictColors[data.ai_verdict.verdict_color] || verdictColors.slate : verdictColors.slate;

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-black/70 backdrop-blur-md z-50"
                    />

                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 40 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 40 }}
                        transition={{ type: "spring", damping: 25, stiffness: 300 }}
                        className="fixed inset-4 md:inset-auto md:left-1/2 md:top-1/2 md:-translate-x-1/2 md:-translate-y-1/2 md:w-[900px] md:max-h-[90vh] bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 rounded-3xl border border-slate-700/50 shadow-2xl z-50 overflow-hidden flex flex-col"
                    >
                        {/* Premium Header */}
                        <div className="relative overflow-hidden">
                            {/* Background gradient effect */}
                            <div className={`absolute inset-0 bg-gradient-to-r ${vColors.bg} opacity-50`} />
                            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0wIDBoNjB2NjBIMHoiLz48cGF0aCBkPSJNMzYuNSAzMGExLjUgMS41IDAgMSAwIDMgMCAxLjUgMS41IDAgMCAwLTMgMHptLTE1IDBhMS41IDEuNSAwIDEgMCAzIDAgMS41IDEuNSAwIDAgMC0zIDB6IiBmaWxsPSJyZ2JhKDI1NSwyNTUsMjU1LDAuMDUpIi8+PC9nPjwvc3ZnPg==')] opacity-30" />

                            <div className="relative p-5 flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <motion.div
                                        className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${vColors.bg} ${vColors.border} border flex items-center justify-center shadow-lg ${vColors.glow}`}
                                        whileHover={{ scale: 1.05 }}
                                    >
                                        <span className="text-white font-bold text-lg">{ticker.slice(0, 4)}</span>
                                    </motion.div>
                                    <div>
                                        <h2 className="text-2xl font-bold text-white">{ticker}</h2>
                                        {data?.company_name && (
                                            <p className="text-sm font-medium text-slate-300">{data.company_name}</p>
                                        )}
                                        <p className="text-xs text-slate-400">{data?.sector || 'Carregando...'}</p>
                                    </div>
                                </div>

                                <div className="flex items-center gap-4">
                                    {data && (
                                        <>
                                            <div className="text-right">
                                                <p className="text-3xl font-bold text-white">R$ {data.price.toFixed(2)}</p>
                                                <p className={`text-sm flex items-center justify-end gap-1 ${data.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                    {data.change >= 0 ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                                                    {Math.abs(data.change).toFixed(2)}%
                                                </p>
                                            </div>
                                            <motion.div
                                                className={`px-4 py-2 rounded-xl border ${vColors.border} bg-gradient-to-r ${vColors.bg}`}
                                                whileHover={{ scale: 1.02 }}
                                            >
                                                <span className={`text-lg font-bold ${vColors.text}`}>
                                                    {data.ai_verdict.verdict_icon} {data.ai_verdict.recommendation}
                                                </span>
                                            </motion.div>
                                        </>
                                    )}
                                    <button onClick={onClose} className="p-2 hover:bg-slate-700/50 rounded-xl transition-colors">
                                        <X className="w-6 h-6 text-slate-400" />
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* Tabs */}
                        <div className="relative px-5 pb-0 flex gap-1">
                            {(['resumo', 'fundamental', 'tecnico'] as const).map((tab) => (
                                <button
                                    key={tab}
                                    onClick={() => setActiveTab(tab)}
                                    className={`px-5 py-2.5 rounded-t-xl text-sm font-medium transition-all ${activeTab === tab
                                        ? 'bg-slate-800 text-white border-t border-x border-slate-700'
                                        : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                                        }`}
                                >
                                    {tab === 'resumo' && <><Sparkles className="w-4 h-4 inline mr-1.5" />Resumo AI</>}
                                    {tab === 'fundamental' && <><DollarSign className="w-4 h-4 inline mr-1.5" />Fundamentalista</>}
                                    {tab === 'tecnico' && <><Activity className="w-4 h-4 inline mr-1.5" />Técnico</>}
                                </button>
                            ))}
                        </div>


                        {/* Content */}
                        <div className="flex-1 overflow-y-auto bg-slate-800 border-t border-slate-700">
                            {loading && (
                                <div className="flex items-center justify-center py-20">
                                    <div className="text-center">
                                        <Loader2 className="w-10 h-10 text-cyan-400 animate-spin mx-auto mb-3" />
                                        <p className="text-slate-400">Analisando {ticker}...</p>
                                    </div>
                                </div>
                            )}

                            {error && (
                                <div className="p-6">
                                    <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-center">
                                        {error}
                                    </div>
                                </div>
                            )}

                            {data && !loading && (
                                <div className="p-5">
                                    <AnimatePresence mode="wait">
                                        {/* RESUMO TAB */}
                                        {activeTab === 'resumo' && (
                                            <motion.div
                                                key="resumo"
                                                initial={{ opacity: 0, x: -20 }}
                                                animate={{ opacity: 1, x: 0 }}
                                                exit={{ opacity: 0, x: 20 }}
                                                className="space-y-5"
                                            >
                                                {/* AI Verdict Card */}
                                                <div className={`relative p-5 rounded-2xl border ${vColors.border} bg-gradient-to-br ${vColors.bg} overflow-hidden`}>
                                                    <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-white/5 to-transparent rounded-bl-full" />
                                                    <div className="relative">
                                                        <div className="flex items-start justify-between mb-4">
                                                            <div>
                                                                <p className="text-slate-400 text-xs uppercase tracking-wider mb-1">Análise AI NorteAções</p>
                                                                <h3 className={`text-2xl font-bold ${vColors.text}`}>
                                                                    {data.ai_verdict.verdict_icon} {data.ai_verdict.verdict}
                                                                </h3>
                                                            </div>
                                                            <div className="flex gap-2">
                                                                <div className="text-center px-3 py-1 rounded-lg bg-slate-900/50">
                                                                    <p className="text-xs text-slate-500">Fund</p>
                                                                    <p className={`font-bold ${data.ai_verdict.fund_score >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                                        {data.ai_verdict.fund_score > 0 ? '+' : ''}{data.ai_verdict.fund_score}
                                                                    </p>
                                                                </div>
                                                                <div className="text-center px-3 py-1 rounded-lg bg-slate-900/50">
                                                                    <p className="text-xs text-slate-500">Tech</p>
                                                                    <p className={`font-bold ${data.ai_verdict.tech_score >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                                        {data.ai_verdict.tech_score > 0 ? '+' : ''}{data.ai_verdict.tech_score}
                                                                    </p>
                                                                </div>
                                                            </div>
                                                        </div>
                                                        <p className="text-slate-300 text-sm leading-relaxed">{data.ai_verdict.summary}</p>

                                                        {/* Highlights & Concerns */}
                                                        <div className="grid md:grid-cols-2 gap-4 mt-4">
                                                            <div className="space-y-2">
                                                                {data.ai_verdict.highlights.map((h, i) => (
                                                                    <div key={i} className="flex items-center gap-2 text-sm">
                                                                        <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                                                                        <span className="text-green-300">{h}</span>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                            <div className="space-y-2">
                                                                {data.ai_verdict.concerns.map((c, i) => (
                                                                    <div key={i} className="flex items-center gap-2 text-sm">
                                                                        <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                                                                        <span className="text-amber-300">{c}</span>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Quick Stats */}
                                                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                                    <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700/50">
                                                        <div className="flex items-center justify-between mb-2">
                                                            <Crosshair className="w-5 h-5 text-cyan-400" />
                                                            <span className="text-[10px] text-slate-500 uppercase">Super Score</span>
                                                        </div>
                                                        <p className="text-2xl font-bold text-cyan-400">{data.fundamental.scores.super_score}</p>
                                                    </div>
                                                    <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700/50">
                                                        <div className="flex items-center justify-between mb-2">
                                                            <Rocket className="w-5 h-5 text-amber-400" />
                                                            <span className="text-[10px] text-slate-500 uppercase">Ranking Setor</span>
                                                        </div>
                                                        <p className="text-2xl font-bold text-white">#{data.sector_ranking.rank}<span className="text-sm text-slate-500">/{data.sector_ranking.total}</span></p>
                                                    </div>
                                                    <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700/50">
                                                        <div className="flex items-center justify-between mb-2">
                                                            <Clock className="w-5 h-5 text-green-400" />
                                                            <span className="text-[10px] text-slate-500 uppercase">Fair Value</span>
                                                        </div>
                                                        <p className="text-2xl font-bold text-white">
                                                            R$ {data.fair_value.average?.toFixed(2) || '-'}
                                                        </p>
                                                        {data.fair_value.upside !== undefined && (
                                                            <p className={`text-xs ${data.fair_value.upside >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                                {data.fair_value.upside >= 0 ? '↑' : '↓'} {Math.abs(data.fair_value.upside)}% upside
                                                            </p>
                                                        )}
                                                    </div>
                                                    <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700/50">
                                                        <RSIGauge value={data.technical.indicators.rsi} />
                                                    </div>
                                                </div>

                                                {/* Fair Value Methods */}
                                                <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700/50">
                                                    <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                                                        <DollarSign className="w-4 h-4 text-green-400" />
                                                        Estimativas de Preço Justo
                                                    </h4>
                                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                                        {data.fair_value.graham && (
                                                            <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                                                                <p className="text-xs text-slate-500 mb-1">Graham</p>
                                                                <p className="text-lg font-bold text-white">R$ {data.fair_value.graham}</p>
                                                            </div>
                                                        )}
                                                        {data.fair_value.bazin && (
                                                            <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                                                                <p className="text-xs text-slate-500 mb-1">Bazin (DY 6%)</p>
                                                                <p className="text-lg font-bold text-white">R$ {data.fair_value.bazin}</p>
                                                            </div>
                                                        )}
                                                        {data.fair_value.earnings && (
                                                            <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                                                                <p className="text-xs text-slate-500 mb-1">P/L Justo (12x)</p>
                                                                <p className="text-lg font-bold text-white">R$ {data.fair_value.earnings}</p>
                                                            </div>
                                                        )}
                                                        {data.fair_value.roe_based && (
                                                            <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                                                                <p className="text-xs text-slate-500 mb-1">ROE-Based</p>
                                                                <p className="text-lg font-bold text-white">R$ {data.fair_value.roe_based}</p>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </motion.div>
                                        )}

                                        {/* FUNDAMENTAL TAB */}
                                        {activeTab === 'fundamental' && (
                                            <motion.div
                                                key="fundamental"
                                                initial={{ opacity: 0, x: -20 }}
                                                animate={{ opacity: 1, x: 0 }}
                                                exit={{ opacity: 0, x: 20 }}
                                                className="space-y-5"
                                            >
                                                {/* Key Metrics Grid */}
                                                <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
                                                    {[
                                                        { label: 'P/L', value: data.fundamental.p_l, suffix: '', color: data.fundamental.p_l > 0 && data.fundamental.p_l < 15 ? 'text-green-400' : 'text-white' },
                                                        { label: 'P/VP', value: data.fundamental.p_vp, suffix: '', color: data.fundamental.p_vp < 1.5 ? 'text-green-400' : 'text-white' },
                                                        { label: 'Div. Yield', value: data.fundamental.dividend_yield, suffix: '%', color: data.fundamental.dividend_yield >= 6 ? 'text-amber-400' : 'text-white' },
                                                        { label: 'ROE', value: data.fundamental.roe, suffix: '%', color: data.fundamental.roe >= 20 ? 'text-emerald-400' : 'text-white' },
                                                        { label: 'ROIC', value: data.fundamental.roic, suffix: '%', color: data.fundamental.roic >= 15 ? 'text-blue-400' : 'text-white' },
                                                        { label: 'Margem Líq.', value: data.fundamental.margem_liquida, suffix: '%', color: 'text-purple-400' },
                                                    ].map((metric, i) => (
                                                        <div key={i} className="bg-slate-900/50 rounded-xl p-3 border border-slate-700/50 text-center">
                                                            <p className="text-[10px] text-slate-500 uppercase mb-1">{metric.label}</p>
                                                            <p className={`text-xl font-bold ${metric.color}`}>
                                                                {metric.value.toFixed(1)}{metric.suffix}
                                                            </p>
                                                        </div>
                                                    ))}
                                                </div>

                                                {/* Strategy Scores */}
                                                <div className="bg-slate-900/50 rounded-xl p-5 border border-slate-700/50">
                                                    <h4 className="text-sm font-semibold text-white mb-4">Scores por Estratégia</h4>
                                                    <div className="flex justify-around items-end">
                                                        {[
                                                            { label: 'Graham', value: data.fundamental.scores.graham, color: 'green' },
                                                            { label: 'Greenblatt', value: data.fundamental.scores.greenblatt, color: 'cyan' },
                                                            { label: 'Bazin', value: data.fundamental.scores.bazin, color: 'amber' },
                                                            { label: 'Qualidade', value: data.fundamental.scores.qualidade, color: 'purple' },
                                                        ].map((score) => (
                                                            <div key={score.label} className="flex flex-col items-center">
                                                                <CircularProgress value={score.value} max={10} size={70} color={score.color} />
                                                                <p className="text-xs text-slate-400 mt-2">{score.label}</p>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>

                                                {/* Sector Comparison */}
                                                <div className="bg-slate-900/50 rounded-xl p-5 border border-slate-700/50">
                                                    <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                                                        <Rocket className="w-4 h-4 text-amber-400" />
                                                        Comparação no Setor: {data.sector}
                                                    </h4>
                                                    <div className="flex items-center gap-4 mb-4">
                                                        <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                                                            <motion.div
                                                                className="h-full bg-gradient-to-r from-amber-500 to-amber-400"
                                                                initial={{ width: 0 }}
                                                                animate={{ width: `${data.sector_ranking.percentile}%` }}
                                                                transition={{ duration: 1, delay: 0.3 }}
                                                            />
                                                        </div>
                                                        <span className="text-amber-400 font-bold">Top {100 - data.sector_ranking.percentile}%</span>
                                                    </div>
                                                    <p className="text-sm text-slate-400">
                                                        <strong className="text-white">{ticker}</strong> está em <strong className="text-amber-400">#{data.sector_ranking.rank}</strong> de {data.sector_ranking.total} empresas no setor
                                                    </p>
                                                </div>
                                            </motion.div>
                                        )}

                                        {/* TECNICO TAB */}
                                        {activeTab === 'tecnico' && (
                                            <motion.div
                                                key="tecnico"
                                                initial={{ opacity: 0, x: -20 }}
                                                animate={{ opacity: 1, x: 0 }}
                                                exit={{ opacity: 0, x: 20 }}
                                                className="space-y-6"
                                            >
                                                <div className="bg-slate-900/50 rounded-2xl border border-slate-700/50 p-1 h-[500px] overflow-hidden">
                                                    <AdvancedRealTimeChart
                                                        theme="dark"
                                                        symbol={`BMFBOVESPA:${ticker}`}
                                                        autosize
                                                        locale="br"
                                                        interval="D"
                                                        timezone="America/Sao_Paulo"
                                                        style="1"
                                                        toolbar_bg="#1e293b"
                                                        hide_side_toolbar={false}
                                                        details={false}
                                                        hotlist={false}
                                                        calendar={false}
                                                    />
                                                </div>

                                                {/* Technical Indicators */}
                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                    {/* RSI Card */}
                                                    <div className={`p-5 rounded-2xl border border-slate-700/50 bg-gradient-to-br from-slate-800 to-slate-900`}>
                                                        <h3 className="text-slate-400 text-sm font-medium mb-4 flex items-center gap-2">
                                                            <Activity className="w-4 h-4" /> RSI (14)
                                                        </h3>
                                                        <div className="flex justify-center">
                                                            <RSIGauge value={data.technical.indicators.rsi} />
                                                        </div>
                                                    </div>

                                                    {/* Moving Averages */}
                                                    <div className="p-5 rounded-2xl border border-slate-700/50 bg-gradient-to-br from-slate-800 to-slate-900">
                                                        <h3 className="text-slate-400 text-sm font-medium mb-4 flex items-center gap-2">
                                                            <TrendingUp className="w-4 h-4" /> Médias Móveis
                                                        </h3>
                                                        <div className="space-y-4">
                                                            <div className="flex justify-between items-center">
                                                                <span className="text-sm text-slate-400">SMA 20</span>
                                                                <span className="font-mono font-bold text-white">R$ {data.technical.sma20?.toFixed(2) || 'N/A'}</span>
                                                            </div>
                                                            <div className="flex justify-between items-center">
                                                                <span className="text-sm text-slate-400">SMA 50</span>
                                                                <span className="font-mono font-bold text-white">R$ {data.technical.sma50?.toFixed(2) || 'N/A'}</span>
                                                            </div>
                                                            <div className="flex justify-between items-center">
                                                                <span className="text-sm text-slate-400">EMA 200</span>
                                                                <div className="text-right">
                                                                    <span className="font-mono font-bold text-white block">R$ {data.technical.indicators.ema200?.toFixed(2) || 'N/A'}</span>
                                                                    <span className={`text-[10px] ${data.price > (data.technical.indicators.ema200 || 0) ? 'text-green-400' : 'text-red-400'}`}>
                                                                        {data.timing.distance_to_ema200 && data.timing.distance_to_ema200 > 0 ? '+' : ''}
                                                                        {(data.timing.distance_to_ema200 || 0).toFixed(1)}%
                                                                    </span>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </motion.div>
                                        )}
                                    </AnimatePresence>
                                </div>
                            )}
                        </div>

                        {/* Footer */}
                        <div className="p-4 border-t border-slate-700 bg-slate-900/50 flex items-center justify-between">
                            <a
                                href={`https://www.google.com/search?q=${ticker}+RI`}
                                target="_blank"
                                rel="noreferrer"
                                className="flex items-center gap-2 text-sm text-cyan-400 hover:text-cyan-300 transition-colors"
                            >
                                <ExternalLink className="w-4 h-4" />
                                Visitar RI da Empresa
                            </a>
                            <a
                                href={`https://www.tradingview.com/chart/?symbol=BMFBOVESPA:${ticker}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-2 text-sm text-cyan-400 hover:text-cyan-300 transition-colors"
                            >
                                <ExternalLink className="w-4 h-4" />
                                Ver no TradingView
                            </a>
                            <div className="flex items-center gap-2">
                                <span className="text-xs text-slate-500">Análise automatizada • Não é recomendação</span>
                                <button
                                    onClick={onClose}
                                    className="px-5 py-2 bg-slate-700 hover:bg-slate-600 rounded-xl text-white text-sm font-medium transition-colors"
                                >
                                    Fechar
                                </button>
                            </div>
                        </div>
                    </motion.div>
                </>
            )
            }
        </AnimatePresence >
    );
}
