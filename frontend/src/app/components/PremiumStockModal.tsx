'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    ChevronUp,
    ChevronDown,
    Rocket,
    AlertTriangle,
    TrendingUp,
    Activity,
    DollarSign,
    Sparkles,
    X,
    Loader2,
    ExternalLink,
    CheckCircle,
    Target,
    BarChart3,
    Zap
} from 'lucide-react';
import { AdvancedRealTimeChart } from 'react-ts-tradingview-widgets';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// --- Interfaces ---
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
        lpa: number;
        vpa: number;
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
}

interface Props {
    ticker: string;
    isOpen: boolean;
    onClose: () => void;
}

// --- Helper Functions ---
const formatPrice = (val?: number | null) => {
    if (val === undefined || val === null || isNaN(val) || val === 0) return '---';
    return val.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

const formatPercent = (val?: number) => {
    if (val === undefined || isNaN(val)) return '---';
    return `${val > 0 ? '+' : ''}${val.toFixed(2)}%`;
};

// --- Shared Components ---

// Bento Card Wrapper
const BentoCard = ({ children, className = "", noPadding = false }: { children: React.ReactNode; className?: string; noPadding?: boolean }) => (
    <div className={`bg-slate-900/60 backdrop-blur-md border border-white/5 rounded-3xl overflow-hidden shadow-xl transition-all duration-300 hover:border-white/10 ${noPadding ? '' : 'p-5 sm:p-6 lg:p-7'} ${className}`}>
        {children}
    </div>
);

// Minimalist Circular Progress (Doughnut)
const MiniDoughnut = ({ value, label, color = "emerald" }: { value: number; label: string; color?: string }) => {
    const radius = 28;
    const circumference = 2 * Math.PI * radius;
    const safeValue = isNaN(value) ? 0 : Math.min(Math.max(value, 0), 10);
    const strokeDashoffset = circumference - (safeValue / 10) * circumference;

    const colorMap: Record<string, string> = {
        emerald: 'stroke-emerald-500',
        amber: 'stroke-amber-500',
        rose: 'stroke-rose-500',
        blue: 'stroke-blue-500',
        purple: 'stroke-purple-500'
    };

    return (
        <div className="flex flex-col items-center gap-2">
            <div className="relative w-14 h-14 lg:w-16 lg:h-16">
                <svg className="w-full h-full transform -rotate-90">
                    <circle
                        cx="50%" cy="50%" r={radius}
                        className="stroke-slate-800" strokeWidth="5" fill="transparent"
                    />
                    <motion.circle
                        cx="50%" cy="50%" r={radius}
                        className={`${colorMap[color]} drop-shadow-[0_0_8px_rgba(0,0,0,0.5)]`}
                        strokeWidth="5"
                        fill="transparent"
                        strokeDasharray={circumference}
                        initial={{ strokeDashoffset: circumference }}
                        animate={{ strokeDashoffset }}
                        transition={{ duration: 1.5, ease: "easeOut" }}
                        strokeLinecap="round"
                    />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-sm font-black text-white tabular-nums">
                        {isNaN(value) ? '---' : value.toFixed(1)}
                    </span>
                </div>
            </div>
            <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest text-center">{label}</span>
        </div>
    );
};

// RSI Gauge - Bento Style
const RSIGauge = ({ value }: { value: number | null }) => {
    if (value === null) return <div className="text-slate-500 text-sm">N/A</div>;
    const percentage = value;

    return (
        <div className="flex flex-col items-center w-full max-w-[180px] mx-auto">
            <div className="relative w-full h-1.5 bg-slate-800 rounded-full overflow-hidden mt-2">
                <div className="absolute inset-0 flex">
                    <div className="w-[30%] h-full border-r border-slate-900/10 bg-emerald-500/20" />
                    <div className="w-[40%] h-full border-r border-slate-900/10 bg-blue-500/20" />
                    <div className="w-[30%] h-full bg-rose-500/20" />
                </div>
                <motion.div
                    className="absolute top-0 bottom-0 w-1 bg-white shadow-[0_0_10px_white] z-10"
                    initial={{ left: "50%" }}
                    animate={{ left: `${percentage}%` }}
                    transition={{ type: "spring", stiffness: 50 }}
                />
            </div>
            <div className="flex justify-between w-full mt-2.5 text-[8px] lg:text-[9px] text-slate-500 font-bold uppercase tracking-tighter">
                <span>Vendido</span>
                <span className="text-white bg-slate-800 px-1.5 py-0.5 rounded shadow-inner">{value.toFixed(0)}</span>
                <span>Comprado</span>
            </div>
        </div>
    );
};

// --- Main Component ---
export default function PremiumStockModal({ ticker, isOpen, onClose }: Props) {
    const [data, setData] = useState<StockAnalysis | null>(null);
    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState<'resumo' | 'fundamental' | 'tecnico'>('resumo');

    useEffect(() => {
        if (isOpen && ticker) fetchData();
    }, [isOpen, ticker]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const res = await fetch(`${API_URL}/stock/${ticker}/full-analysis`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const json = await res.json();
            setData(json);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/90 backdrop-blur-2xl z-50 flex items-center justify-center p-2 lg:p-6"
                onClick={onClose}
            >
                <motion.div
                    initial={{ opacity: 0, scale: 0.98, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.98, y: 20 }}
                    transition={{ type: "spring", damping: 25, stiffness: 200 }}
                    className="w-full max-w-6xl h-full max-h-[96vh] bg-[#020617] border border-white/10 rounded-[32px] overflow-hidden flex flex-col shadow-[0_0_80px_rgba(0,0,0,1)] relative"
                    onClick={(e) => e.stopPropagation()}
                >
                    {/* Header Section - Viewport Economy Scaling */}
                    <div className="relative pt-6 px-10 pb-4 bg-gradient-to-b from-slate-900/30 to-transparent shrink-0">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
                            <div className="flex items-center gap-6">
                                <div className="w-14 h-14 bg-gradient-to-br from-emerald-500/20 to-emerald-600/5 border border-emerald-500/20 rounded-[18px] flex items-center justify-center shrink-0 shadow-xl">
                                    <span className="text-xl font-black text-emerald-400 tracking-tighter">{ticker.slice(0, 4)}</span>
                                </div>
                                <div className="space-y-1">
                                    <div className="flex flex-wrap items-center gap-3">
                                        <h1 className="text-3xl font-black text-white tracking-tighter leading-none">{ticker}</h1>
                                        <div className="px-3.5 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full backdrop-blur-md self-center shadow-md">
                                            <span className="text-[10px] font-black text-emerald-400 uppercase tracking-[0.2em] whitespace-nowrap">
                                                {data?.ai_verdict?.recommendation || 'Analisando...'}
                                            </span>
                                        </div>
                                    </div>
                                    <p className="text-[13px] font-bold text-slate-400 tracking-tight truncate max-w-[200px] sm:max-w-md">
                                        {data?.company_name || 'Alinhando vetores de mercado...'}
                                    </p>
                                </div>
                            </div>

                            <div className="flex items-center justify-between sm:justify-end gap-10">
                                <div className="text-right flex flex-col items-end">
                                    <div className="text-3xl font-black text-white tabular-nums tracking-tighter">
                                        R$ {formatPrice(data?.price)}
                                    </div>
                                    <div className={`mt-1 flex items-center gap-1.5 text-sm font-black tabular-nums px-2.5 py-1 rounded-full ${data && data.change >= 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}`}>
                                        {data && data.change >= 0 ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                                        {formatPercent(data?.change)}
                                    </div>
                                </div>
                                <button onClick={onClose} className="p-3 bg-slate-900/60 hover:bg-slate-800 border border-white/10 rounded-full text-slate-400 hover:text-white transition-all group shrink-0">
                                    <X className="w-6 h-6 group-hover:rotate-90 transition-transform duration-500" />
                                </button>
                            </div>
                        </div>

                        {/* Navigation Tabs - More Compact */}
                        <div className="mt-6 flex gap-10 border-b border-white/5 overflow-x-auto no-scrollbar">
                            {[
                                { id: 'resumo', label: 'Dashboard IA', icon: Sparkles },
                                { id: 'fundamental', label: 'Fundamentalista', icon: BarChart3 },
                                { id: 'tecnico', label: 'Indicadores', icon: Zap }
                            ].map((tab) => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id as any)}
                                    className={`relative pb-3 flex items-center gap-2.5 text-[13px] font-black transition-all whitespace-nowrap px-1 ${activeTab === tab.id ? 'text-white' : 'text-slate-500 hover:text-slate-300'}`}
                                >
                                    <tab.icon className={`w-4 h-4 ${activeTab === tab.id ? 'text-emerald-400' : 'text-current'}`} />
                                    {tab.label}
                                    {activeTab === tab.id && (
                                        <motion.div layoutId="activeTab" className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-500 rounded-full shadow-[0_0_15px_rgba(16,185,129,0.8)]" />
                                    )}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Content Section - Strict no-overflow on main modal */}
                    <div className="flex-1 overflow-hidden flex flex-col px-10 pb-6 pt-4">
                        {loading ? (
                            <div className="flex-1 flex flex-col items-center justify-center gap-6">
                                <div className="relative">
                                    <div className="w-16 h-16 rounded-full border-4 border-slate-800 border-t-emerald-500 animate-spin" />
                                    <Sparkles className="w-7 h-7 text-emerald-400 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                                </div>
                                <p className="text-slate-500 text-xs font-black uppercase tracking-[0.4em] animate-pulse">Compilando Dados...</p>
                            </div>
                        ) : data && (
                            <AnimatePresence mode="wait">
                                {activeTab === 'resumo' && (
                                    <motion.div
                                        key="resumo"
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -10 }}
                                        className="flex-1 grid grid-cols-12 gap-6 min-h-0"
                                    >
                                        {/* Main AI Card - Using flex-1 internally */}
                                        <div className="col-span-12 lg:col-span-8 flex flex-col min-h-0">
                                            <BentoCard className="flex-1 flex flex-col overflow-hidden bg-[#030712]/60 border-white/5 p-8 lg:p-10 relative group">
                                                {/* Ambient Backgrounds */}
                                                <div className="absolute top-0 right-0 -mr-20 -mt-20 w-[300px] h-[300px] bg-emerald-500/10 rounded-full blur-[100px] opacity-10 pointer-events-none" />

                                                <div className="shrink-0">
                                                    <div className="flex items-start justify-between gap-6 mb-8">
                                                        <div className="space-y-4">
                                                            <div className="flex items-center gap-3 text-emerald-400">
                                                                <div className="p-2.5 bg-emerald-500/15 rounded-xl border border-emerald-500/20 shadow-xl">
                                                                    <Sparkles className="w-5 h-5" />
                                                                </div>
                                                                <span className="text-[11px] font-black uppercase tracking-[0.4em]">Algoritmo NorteAções</span>
                                                            </div>
                                                            <div className={`inline-flex px-5 py-2 rounded-full border shadow-xl backdrop-blur-3xl ${data.ai_verdict.verdict.toLowerCase().includes('risco') || data.ai_verdict.verdict.toLowerCase().includes('venda') ? 'bg-rose-500/20 border-rose-500/30 text-rose-400' : 'bg-emerald-500/20 border-emerald-500/30 text-emerald-400'}`}>
                                                                <span className="text-lg font-black uppercase tracking-tight">{data.ai_verdict.verdict}</span>
                                                            </div>
                                                        </div>
                                                        <div className="flex gap-4">
                                                            <div className="px-6 py-4 bg-slate-950/90 border border-white/10 rounded-[20px] text-center shadow-xl">
                                                                <p className="text-[9px] text-slate-500 uppercase font-black tracking-[0.2em] mb-1.5">Score Fund</p>
                                                                <p className="text-2xl font-black text-emerald-400">+{data.ai_verdict.fund_score}</p>
                                                            </div>
                                                            <div className="px-6 py-4 bg-slate-950/90 border border-white/10 rounded-[20px] text-center shadow-xl">
                                                                <p className="text-[9px] text-slate-500 uppercase font-black tracking-[0.2em] mb-1.5">Score Tech</p>
                                                                <p className="text-2xl font-black text-blue-400">+{data.ai_verdict.tech_score}</p>
                                                            </div>
                                                        </div>
                                                    </div>

                                                    <p className="text-slate-300 text-lg lg:text-xl leading-[1.6] font-bold mb-8 max-w-4xl tracking-tight">
                                                        {data.ai_verdict?.summary || 'Análise indisponível no momento.'}
                                                    </p>
                                                </div>

                                                <div className="flex-1 min-h-0 pt-8 border-t border-white/5 grid grid-cols-1 sm:grid-cols-2 gap-10 overflow-y-auto custom-scrollbar pr-2">
                                                    <div className="space-y-6">
                                                        <div className="flex items-center gap-4 text-emerald-400 font-black text-xs uppercase tracking-[0.2em]">
                                                            <CheckCircle className="w-6 h-6" />
                                                            Destaques Positivos
                                                        </div>
                                                        <div className="space-y-5">
                                                            {data.ai_verdict.highlights.slice(0, 4).map((h, i) => (
                                                                <div key={i} className="flex items-start gap-4">
                                                                    <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/40 mt-2 shrink-0" />
                                                                    <p className="text-base font-bold text-slate-400 leading-snug">{h}</p>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                    <div className="space-y-6">
                                                        <div className="flex items-center gap-4 text-rose-400 font-black text-xs uppercase tracking-[0.2em]">
                                                            <AlertTriangle className="w-6 h-6" />
                                                            Fatores de Risco
                                                        </div>
                                                        <div className="space-y-5">
                                                            {data.ai_verdict.concerns.slice(0, 4).map((c, i) => (
                                                                <div key={i} className="flex items-start gap-4">
                                                                    <div className="w-2.5 h-2.5 rounded-full bg-rose-500/40 mt-2 shrink-0" />
                                                                    <p className="text-base font-bold text-slate-400 leading-snug">{c}</p>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                </div>
                                            </BentoCard>
                                        </div>

                                        {/* Right Column Metrics - FLEX COLUMN */}
                                        <div className="col-span-12 lg:col-span-4 flex flex-col gap-6 min-h-0">
                                            <BentoCard className="flex-1 flex flex-col items-center justify-center text-center gap-6 bg-slate-900/20 border-white/5 min-h-0">
                                                <MiniDoughnut value={data.fundamental.scores.super_score} label="SUPER SCORE" color="emerald" />
                                            </BentoCard>

                                            <BentoCard className="flex-1 flex flex-col items-center justify-center text-center gap-6 bg-slate-900/20 border-white/5 min-h-0">
                                                <div className="relative">
                                                    <div className="w-16 h-16 bg-blue-500/10 rounded-full flex items-center justify-center border border-blue-500/20 shadow-xl group-hover:scale-105 transition-transform">
                                                        <Rocket className="w-7 h-7 text-blue-400" />
                                                    </div>
                                                    <div className="absolute -top-1 -right-1 w-8 h-8 bg-blue-600 text-white rounded-full text-xs font-black flex items-center justify-center shadow-2xl border-2 border-slate-950">
                                                        #{data.sector_ranking.rank}
                                                    </div>
                                                </div>
                                                <div className="space-y-2">
                                                    <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em]">RANKING SETORIAL</p>
                                                    <p className="text-sm font-black text-slate-100 uppercase tracking-tighter truncate max-w-[160px]">{data.sector}</p>
                                                </div>
                                            </BentoCard>

                                            <BentoCard className="flex-[1.2] bg-gradient-to-br from-indigo-950/40 to-[#020617] border-indigo-500/30 relative flex flex-col justify-center p-8 min-h-0">
                                                <div className="absolute top-0 right-0 w-48 h-48 bg-indigo-500/15 blur-[80px] pointer-events-none" />
                                                <div className="flex items-center justify-between mb-8">
                                                    <div className="flex items-center gap-3">
                                                        <div className="p-2.5 bg-indigo-500/20 rounded-xl border border-indigo-500/20">
                                                            <Target className="w-6 h-6 text-indigo-400" />
                                                        </div>
                                                        <p className="text-[11px] font-black text-indigo-300 uppercase tracking-[0.3em]">Fair Value</p>
                                                    </div>
                                                    <div className={`px-4 py-1.5 rounded-full text-xs font-black shrink-0 ${Number(data.fair_value.upside) >= 0 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}`}>
                                                        {formatPercent(data.fair_value.upside)}
                                                    </div>
                                                </div>
                                                <div className="mt-auto">
                                                    <div className="flex items-baseline gap-2">
                                                        <span className="text-xl font-black text-slate-500 tracking-tighter uppercase">R$</span>
                                                        <p className="text-5xl font-black text-white tabular-nums tracking-tighter">
                                                            {formatPrice(data.fair_value.average)}
                                                        </p>
                                                    </div>
                                                    <p className="text-[10px] font-black text-slate-500 mt-4 flex items-center gap-3 uppercase tracking-[0.2em]">
                                                        <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-pulse shadow-sm" />
                                                        Projeção Alvo (Média)
                                                    </p>
                                                </div>
                                            </BentoCard>
                                        </div>

                                        {/* Bottom Valuation Strip - Viewport Efficiency */}
                                        <div className="col-span-12 shrink-0">
                                            <BentoCard noPadding className="bg-[#030712]/90 border-white/5 shadow-2xl">
                                                <div className="p-8 lg:p-10 flex flex-col lg:flex-row items-center justify-between gap-8 lg:gap-6">
                                                    <div className="flex items-center gap-6 shrink-0">
                                                        <div className="p-4 bg-slate-900/80 rounded-[22px] border border-white/10 shadow-xl">
                                                            <DollarSign className="w-7 h-7 text-slate-200" />
                                                        </div>
                                                        <div className="space-y-1">
                                                            <span className="text-xs font-black text-white uppercase tracking-[0.3em]">Modelos Quant</span>
                                                            <p className="text-[10px] text-slate-600 font-bold uppercase tracking-[0.2em]">Precificação Média</p>
                                                        </div>
                                                    </div>

                                                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-14 w-full lg:w-auto">
                                                        {[
                                                            { label: 'GRAHAM', value: data.fair_value?.graham },
                                                            { label: 'BAZIN (6%)', value: data.fair_value?.bazin },
                                                            { label: 'P/L (12X)', value: data.fair_value?.earnings },
                                                            { label: 'ROE-SIDE', value: data.fair_value?.roe_based }
                                                        ].map((m, i) => (
                                                            <div key={i} className="flex flex-col items-end px-4 border-r border-white/5 last:border-0 min-w-fit hover:bg-white/5 transition-colors py-2 rounded-xl">
                                                                <p className="text-[10px] font-black text-slate-500 tracking-[0.2em] mb-2 uppercase">{m.label}</p>
                                                                <div className="flex items-baseline gap-1.5">
                                                                    <span className="text-[11px] text-slate-600 font-black">R$</span>
                                                                    <p className="text-xl font-black text-slate-100 tabular-nums whitespace-nowrap tracking-tighter">
                                                                        {formatPrice(m.value)}
                                                                    </p>
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            </BentoCard>
                                        </div>
                                    </motion.div>
                                )}

                                {activeTab === 'fundamental' && (
                                    <motion.div
                                        key="fundamental"
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -10 }}
                                        className="flex-1 flex flex-col gap-8 min-h-0 overflow-y-auto custom-scrollbar pr-2"
                                    >
                                        <BentoCard noPadding className="border-white/5 shadow-2xl bg-[#030712]/40 shrink-0">
                                            <div className="grid grid-cols-2 lg:grid-cols-6 divide-y lg:divide-y-0 lg:divide-x divide-white/10">
                                                {[
                                                    { label: 'P/L Ratio', val: data.fundamental.p_l, suffix: 'x', color: 'text-emerald-400' },
                                                    { label: 'P/VP Ratio', val: data.fundamental.p_vp, suffix: 'x', color: 'text-blue-400' },
                                                    { label: 'Div. Yield', val: data.fundamental.dividend_yield, suffix: '%', color: 'text-amber-400' },
                                                    { label: 'Net ROE', val: data.fundamental.roe, suffix: '%', color: 'text-emerald-400' },
                                                    { label: 'Cap. ROIC', val: data.fundamental.roic, suffix: '%', color: 'text-indigo-400' },
                                                    { label: 'Margin Liq.', val: data.fundamental.margem_liquida, suffix: '%', color: 'text-purple-400' }
                                                ].map((kpi, i) => (
                                                    <div key={i} className="p-8 text-center lg:text-left hover:bg-white/[0.03] transition-all group">
                                                        <p className="text-[10px] font-black text-slate-500 uppercase mb-4 tracking-[0.2em]">{kpi.label}</p>
                                                        <p className={`text-3xl font-black tabular-nums tracking-tighter ${kpi.color}`}>{kpi.val?.toFixed(1)}{kpi.suffix}</p>
                                                    </div>
                                                ))}
                                            </div>
                                        </BentoCard>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 min-h-0">
                                            <BentoCard className="bg-slate-900/10 border-white/10 p-10 flex flex-col">
                                                <h4 className="text-lg font-black text-white mb-10 flex items-center gap-4 uppercase tracking-[0.2em] shrink-0">
                                                    <Target className="w-6 h-6 text-emerald-400" />
                                                    Scores Comparativos
                                                </h4>
                                                <div className="flex-1 grid grid-cols-2 sm:grid-cols-4 gap-10 items-center py-4">
                                                    <MiniDoughnut value={data.fundamental.scores.graham} label="Graham" color="emerald" />
                                                    <MiniDoughnut value={data.fundamental.scores.greenblatt} label="Greenblatt" color="blue" />
                                                    <MiniDoughnut value={data.fundamental.scores.bazin} label="Bazin" color="amber" />
                                                    <MiniDoughnut value={data.fundamental.scores.qualidade} label="Qualidade" color="purple" />
                                                </div>
                                            </BentoCard>

                                            <BentoCard className="flex flex-col bg-slate-900/10 border-white/10 p-10">
                                                <div className="flex items-center justify-between mb-10 overflow-hidden gap-8 shrink-0">
                                                    <h4 className="text-lg font-black text-white flex items-center gap-4 uppercase tracking-[0.2em] shrink-0">
                                                        <BarChart3 className="w-6 h-6 text-indigo-400" />
                                                        Ranking Setorial
                                                    </h4>
                                                    <span className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em] truncate pl-8 border-l border-white/5">{data.sector}</span>
                                                </div>
                                                <div className="flex-1 flex flex-col justify-center space-y-10">
                                                    <div className="relative h-5 bg-slate-950 border border-white/10 rounded-full overflow-hidden shadow-xl">
                                                        <motion.div
                                                            className="absolute inset-y-0 left-0 bg-gradient-to-r from-indigo-600 via-blue-500 to-emerald-400 shadow-[0_0_15px_rgba(79,70,229,0.4)]"
                                                            initial={{ width: 0 }}
                                                            animate={{ width: `${data.sector_ranking.percentile}%` }}
                                                            transition={{ duration: 1.5, ease: "circOut" }}
                                                        />
                                                    </div>
                                                    <div className="flex items-center justify-between gap-6">
                                                        <p className="text-base font-bold text-slate-400">
                                                            Nível Global <span className="text-white font-black text-2xl ml-2">#{data.sector_ranking.rank}</span> de {data.sector_ranking.total}
                                                        </p>
                                                    </div>
                                                </div>
                                            </BentoCard>
                                        </div>
                                    </motion.div>
                                )}

                                {activeTab === 'tecnico' && (
                                    <motion.div
                                        key="tecnico"
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -10 }}
                                        className="flex-1 flex flex-col gap-8 min-h-0"
                                    >
                                        <div className="flex-1 bg-[#020617] border border-white/10 rounded-[30px] overflow-hidden shadow-[0_0_40px_rgba(0,0,0,0.8)] relative group min-h-0">
                                            <AdvancedRealTimeChart
                                                theme="dark"
                                                symbol={`BMFBOVESPA:${ticker}`}
                                                autosize
                                                locale="br"
                                                interval="D"
                                                timezone="America/Sao_Paulo"
                                                style="1"
                                                toolbar_bg="#020617"
                                                hide_side_toolbar={false}
                                                details={false}
                                                hotlist={false}
                                                calendar={false}
                                                container_id="tradingview_premium"
                                            />
                                        </div>
                                        <div className="shrink-0 grid grid-cols-1 md:grid-cols-2 gap-8">
                                            <BentoCard className="bg-slate-900/10 border-white/10 p-8">
                                                <h4 className="text-base font-black text-white mb-8 uppercase tracking-[0.3em] flex items-center gap-4">
                                                    <Activity className="w-5 h-5 text-emerald-500" />
                                                    Relative Strength (RSI)
                                                </h4>
                                                <div className="py-4">
                                                    <RSIGauge value={data.technical.indicators.rsi} />
                                                </div>
                                            </BentoCard>

                                            <BentoCard className="bg-slate-900/10 border-white/10 p-8">
                                                <h4 className="text-base font-black text-white mb-8 uppercase tracking-[0.3em] flex items-center gap-4">
                                                    <TrendingUp className="w-5 h-5 text-blue-500" />
                                                    Tendência de Médias
                                                </h4>
                                                <div className="space-y-4">
                                                    {[
                                                        { label: 'SMA 20', val: data.technical.sma20, color: 'text-blue-400' },
                                                        { label: 'SMA 50', val: data.technical.sma50, color: 'text-emerald-400' },
                                                        { label: 'EMA 200', val: data.technical.indicators?.ema200, color: 'text-amber-400' }
                                                    ].map((ma, i) => (
                                                        <div key={i} className="flex items-center justify-between p-4 bg-[#030712] rounded-[20px] border border-white/10 hover:border-white/20 transition-all shadow-lg">
                                                            <span className="text-[11px] font-black text-slate-500 uppercase tracking-[0.2em]">{ma.label}</span>
                                                            <div className="flex items-baseline gap-1.5">
                                                                <span className="text-[10px] text-slate-600 font-black">R$</span>
                                                                <span className={`text-lg font-black ${ma.color} tabular-nums tracking-tighter`}>{formatPrice(ma.val)}</span>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </BentoCard>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        )}
                    </div>

                    {/* Footer - Minimum Height Viewport Optimization */}
                    <div className="px-10 py-5 border-t border-white/10 bg-[#020617] flex flex-col sm:flex-row items-center justify-between gap-6 relative z-20 shrink-0 shadow-[0_-10px_40px_rgba(0,0,0,0.8)]">
                        <div className="flex flex-wrap justify-center sm:justify-start gap-10">
                            <a href={`https://www.google.com/search?q=${ticker}+RI`} target="_blank" className="text-[11px] flex items-center gap-3 font-black text-slate-600 hover:text-white uppercase tracking-[0.3em] transition-all group">
                                <ExternalLink className="w-4 h-4 group-hover:text-emerald-400" />
                                Investor Relations
                            </a>
                            <a href={`https://br.tradingview.com/symbols/BMFBOVESPA-${ticker}/`} target="_blank" className="text-[11px] flex items-center gap-3 font-black text-slate-600 hover:text-white uppercase tracking-[0.3em] transition-all group">
                                <ExternalLink className="w-4 h-4 group-hover:text-blue-400" />
                                TradingView Terminal
                            </a>
                        </div>
                        <div className="flex items-center gap-8">
                            <div className="hidden lg:block h-6 w-[1px] bg-white/10 mx-2" />
                            <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em] text-center sm:text-right">
                                © NorteAções AI • <span className="text-slate-600 tracking-tighter">ENGINE V2.1 PREMIUM</span>
                            </p>
                        </div>
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
}
