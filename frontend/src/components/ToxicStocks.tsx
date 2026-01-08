'use client';

import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
    Skull,
    AlertTriangle,
    TrendingDown,
    Shield,
    ChevronRight,
    Flame,
    AlertOctagon,
    Activity,
    RefreshCw,
    Check,
    TrendingUp
} from 'lucide-react';
import StatCard from '../app/components/StatCard';

interface Stock {
    papel: string;
    setor?: string;
    cotacao?: number;
    p_l?: number;
    p_vp?: number;
    dividend_yield?: number;
    roe?: number;
    roic?: number;
    margem_liquida?: number;
    div_bruta_patrimonio?: number;
    super_score?: number;
}

interface ToxicStocksProps {
    stocks: Stock[];
    isPremium: boolean;
    onSelectStock: (stock: Stock) => void;
}

type RiskLevel = 'critical' | 'high' | 'medium';
type FilterType = 'all' | 'avoid' | 'short' | 'turnaround';

interface ToxicAnalysis {
    riskLevel: RiskLevel;
    reasons: string[];
    turnaroundPotential: boolean;
    shortCandidate: boolean;
}

const FILTER_CONFIG = {
    all: {
        label: 'Todas',
        icon: Skull,
        color: 'text-white',
        bgActive: 'bg-gradient-to-r from-slate-700 to-slate-600',
        bgInactive: 'bg-slate-800/50',
        borderActive: 'border-white/30',
        borderInactive: 'border-white/10',
        description: 'Todas as ações tóxicas'
    },
    avoid: {
        label: 'Evitar',
        icon: Shield,
        color: 'text-red-400',
        bgActive: 'bg-gradient-to-r from-red-900/60 to-red-800/60',
        bgInactive: 'bg-red-900/20',
        borderActive: 'border-red-500/50',
        borderInactive: 'border-red-500/20',
        description: 'Risco crítico - evitar compra'
    },
    short: {
        label: 'Short',
        icon: TrendingDown,
        color: 'text-purple-400',
        bgActive: 'bg-gradient-to-r from-purple-900/60 to-purple-800/60',
        bgInactive: 'bg-purple-900/20',
        borderActive: 'border-purple-500/50',
        borderInactive: 'border-purple-500/20',
        description: 'Candidatas para venda'
    },
    turnaround: {
        label: 'Turnaround',
        icon: RefreshCw,
        color: 'text-cyan-400',
        bgActive: 'bg-gradient-to-r from-cyan-900/60 to-cyan-800/60',
        bgInactive: 'bg-cyan-900/20',
        borderActive: 'border-cyan-500/50',
        borderInactive: 'border-cyan-500/20',
        description: 'Potencial de recuperação'
    }
};

export default function ToxicStocks({ stocks, isPremium, onSelectStock }: ToxicStocksProps) {
    const [activeFilter, setActiveFilter] = useState<FilterType>('all');

    const analyzeToxicity = (stock: Stock): ToxicAnalysis => {
        const reasons: string[] = [];
        let riskScore = 0;
        let positiveSignals = 0;

        // P/L Analysis
        if (stock.p_l && stock.p_l < 0) {
            reasons.push('P/L negativo (prejuízo)');
            riskScore += 3;
        } else if (stock.p_l && stock.p_l > 100) {
            reasons.push(`P/L muito alto (${stock.p_l.toFixed(0)}x)`);
            riskScore += 2;
        }

        // ROE Analysis
        if (stock.roe && stock.roe < 0) {
            reasons.push(`ROE negativo (${(stock.roe * 100).toFixed(1)}%)`);
            riskScore += 3;
        } else if (stock.roe && stock.roe < 0.05) {
            reasons.push(`ROE baixo (${(stock.roe * 100).toFixed(1)}%)`);
            riskScore += 1;
        }

        // ROIC Analysis
        if (stock.roic && stock.roic < 0) {
            reasons.push(`ROIC negativo (${(stock.roic * 100).toFixed(1)}%)`);
            riskScore += 2;
        }

        // Margin Analysis
        if (stock.margem_liquida && stock.margem_liquida < 0) {
            reasons.push('Margem líquida negativa');
            riskScore += 2;
        }

        // Debt Analysis
        if (stock.div_bruta_patrimonio && stock.div_bruta_patrimonio > 2) {
            reasons.push(`Dívida alta (${stock.div_bruta_patrimonio.toFixed(1)}x patrimônio)`);
            riskScore += 2;
        }

        // Super Score
        if (stock.super_score && stock.super_score < 10) {
            riskScore += 1;
        }

        // Check for turnaround potential (some positive signals)
        if (stock.dividend_yield && stock.dividend_yield > 0.05) {
            positiveSignals++;
        }
        if (stock.p_vp && stock.p_vp < 1) {
            positiveSignals++;
        }

        // Determine risk level
        let riskLevel: RiskLevel = 'medium';
        if (riskScore >= 6) {
            riskLevel = 'critical';
        } else if (riskScore >= 4) {
            riskLevel = 'high';
        }

        // Short candidate: critical risk + high P/L or negative ROE
        const shortCandidate = riskLevel === 'critical' || (stock.p_l && stock.p_l > 50) || (stock.roe && stock.roe < -0.10);

        return {
            riskLevel,
            reasons,
            turnaroundPotential: positiveSignals >= 1,
            shortCandidate: !!shortCandidate
        };
    };

    // Pre-analyze all stocks (Memoized)
    const analyzedStocks = useMemo(() => stocks.map(stock => ({
        stock,
        analysis: analyzeToxicity(stock)
    })), [stocks]);

    // Apply filter
    const filteredStocks = analyzedStocks.filter(({ analysis }) => {
        switch (activeFilter) {
            case 'avoid':
                return analysis.riskLevel === 'critical';
            case 'short':
                return analysis.shortCandidate;
            case 'turnaround':
                return analysis.turnaroundPotential;
            default:
                return true;
        }
    }).slice(0, isPremium ? undefined : 3); // Free: 3, Premium: ALL

    const getRiskConfig = (level: RiskLevel) => {
        switch (level) {
            case 'critical':
                return {
                    icon: AlertOctagon,
                    label: 'Crítico',
                    color: 'text-red-500',
                    bgColor: 'bg-red-500/10',
                    borderColor: 'border-red-500/20',
                    gradient: 'from-red-600 to-red-800'
                };
            case 'high':
                return {
                    icon: AlertTriangle,
                    label: 'Alto',
                    color: 'text-orange-500',
                    bgColor: 'bg-orange-500/10',
                    borderColor: 'border-orange-500/20',
                    gradient: 'from-orange-600 to-orange-800'
                };
            case 'medium':
                return {
                    icon: Activity,
                    label: 'Médio',
                    color: 'text-yellow-500',
                    bgColor: 'bg-yellow-500/10',
                    borderColor: 'border-yellow-500/20',
                    gradient: 'from-yellow-600 to-yellow-800'
                };
        }
    };

    return (
        <div className="space-y-6">
            {/* Standardized Header Metrics Grid */}
            <div className="dashboard-stats-grid">
                <StatCard
                    title="Ações com Alerta"
                    value={analyzedStocks.length}
                    icon={Skull}
                    gradient="from-red-500 to-rose-700"
                    tooltip="Ativos com indicadores econômicos negativos ou alto risco operacional."
                />
                <StatCard
                    title="Risco Crítico"
                    value={analyzedStocks.filter(s => s.analysis.riskLevel === 'critical').length}
                    icon={AlertTriangle}
                    gradient="from-orange-500 to-red-600"
                    valueColor="text-red-400"
                />
                <StatCard
                    title="Candidatas Short"
                    value={analyzedStocks.filter(s => s.analysis.shortCandidate).length}
                    icon={TrendingDown}
                    gradient="from-purple-500 to-indigo-600"
                />
            </div>

            {/* Filter Buttons */}
            <div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {(Object.keys(FILTER_CONFIG) as FilterType[]).map((filterKey) => {
                        const config = FILTER_CONFIG[filterKey];
                        const Icon = config.icon;
                        const isActive = activeFilter === filterKey;
                        const count = filterKey === 'all'
                            ? analyzedStocks.length
                            : analyzedStocks.filter(({ analysis }) => {
                                if (filterKey === 'avoid') return analysis.riskLevel === 'critical';
                                if (filterKey === 'short') return analysis.shortCandidate;
                                if (filterKey === 'turnaround') return analysis.turnaroundPotential;
                                return false;
                            }).length;

                        return (
                            <motion.button
                                key={filterKey}
                                onClick={() => setActiveFilter(filterKey)}
                                className={`p-4 rounded-xl border transition-all ${isActive
                                    ? `${config.bgActive} ${config.borderActive}`
                                    : `${config.bgInactive} ${config.borderInactive} hover:border-white/20`
                                    }`}
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                            >
                                <div className="flex items-center gap-2 mb-1">
                                    <Icon className={`w-5 h-5 ${config.color}`} />
                                    <span className={`font-bold ${isActive ? 'text-white' : 'text-white/70'}`}>
                                        {config.label}
                                    </span>
                                    {isActive && (
                                        <Check className="w-4 h-4 text-green-400 ml-auto" />
                                    )}
                                </div>
                                <div className="flex items-center justify-between">
                                    <p className="text-xs text-secondary">{config.description}</p>
                                    <span className={`text-sm font-bold ${config.color}`}>
                                        {count}
                                    </span>
                                </div>
                            </motion.button>
                        );
                    })}
                </div>
            </div>

            {/* Results count & Universal Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredStocks.map(({ stock, analysis }, index) => {
                    const riskConfig = getRiskConfig(analysis.riskLevel);
                    return (
                        <motion.div
                            key={stock.papel}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.03 }}
                            className="universal-asset-card group toxic-highlight"
                            onClick={() => onSelectStock(stock)}
                        >
                            {/* Header: Ticker + Risk & Price */}
                            <div className="flex justify-between items-start mb-1">
                                <div className="flex items-center gap-2">
                                    <h3 className="asset-ticker">{stock.papel}</h3>
                                    <div className={`px-1.5 py-0.5 rounded border text-[10px] font-bold ${riskConfig.bgColor} ${riskConfig.color} ${riskConfig.borderColor}`}>
                                        {riskConfig.label}
                                    </div>
                                </div>
                                <div className="asset-price">
                                    R$ {stock.cotacao?.toFixed(2) || '0.00'}
                                </div>
                            </div>

                            {/* Sector */}
                            <p className="text-[10px] text-white/30 font-bold uppercase tracking-wider mb-4">
                                {stock.setor || 'N/A'}
                            </p>

                            {/* Standardized 3-column Metric Grid */}
                            <div className="grid grid-cols-3 gap-2 py-4 border-y border-white/5 my-2">
                                <div className="text-center">
                                    <p className="card-metric-label">P/L</p>
                                    <p className={`card-metric-value ${stock.p_l && stock.p_l < 0 ? 'text-red-400' : ''}`}>
                                        {stock.p_l?.toFixed(1) || '0.0'}
                                    </p>
                                </div>
                                <div className="text-center border-x border-white/5">
                                    <p className="card-metric-label">DY</p>
                                    <p className="card-metric-value">
                                        {stock.dividend_yield ? (stock.dividend_yield * 100).toFixed(1) : '0'}%
                                    </p>
                                </div>
                                <div className="text-center">
                                    <p className="card-metric-label">ROE</p>
                                    <p className={`card-metric-value ${stock.roe && stock.roe < 0 ? 'text-red-400' : ''}`}>
                                        {stock.roe ? (stock.roe * 100).toFixed(1) : '0'}%
                                    </p>
                                </div>
                            </div>

                            {/* Footer: Compact Alert Tags */}
                            <div className="flex items-center justify-between mt-3">
                                <div className="flex flex-wrap items-center gap-1.5">
                                    {analysis.reasons.map((reason, i) => (
                                        <div key={i} className="p-1.5 rounded-lg bg-white/5 text-red-400 border border-white/5" title={reason}>
                                            <AlertTriangle className="w-3.5 h-3.5" />
                                        </div>
                                    ))}
                                    {analysis.turnaroundPotential && (
                                        <div className="p-1.5 rounded-lg bg-white/5 text-cyan-400 border border-white/5" title="Potencial Turnaround">
                                            <RefreshCw className="w-3.5 h-3.5" />
                                        </div>
                                    )}
                                    {analysis.shortCandidate && (
                                        <div className="p-1.5 rounded-lg bg-white/5 text-purple-400 border border-white/5" title="Candidata Short">
                                            <TrendingDown className="w-3.5 h-3.5" />
                                        </div>
                                    )}
                                </div>

                                <div className="p-2 rounded-lg bg-white/5 text-white/20 group-hover:bg-red-500/10 group-hover:text-red-400 transition-colors">
                                    <Skull className="w-4 h-4" />
                                </div>
                            </div>
                        </motion.div>
                    );
                })}
            </div>

            {filteredStocks.length === 0 && (
                <div className="text-center py-12 text-white/40">
                    Nenhuma ação encontrada com este filtro.
                </div>
            )}
        </div>
    );
}
