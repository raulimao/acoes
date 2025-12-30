'use client';

import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
    Skull,
    AlertTriangle,
    TrendingDown,
    Shield,
    Eye,
    ChevronRight,
    Flame,
    AlertOctagon,
    Activity,
    RefreshCw,
    Check
} from 'lucide-react';

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
            reasons.push(`ROE negativo (${stock.roe.toFixed(1)}%)`);
            riskScore += 3;
        } else if (stock.roe && stock.roe < 5) {
            reasons.push(`ROE baixo (${stock.roe.toFixed(1)}%)`);
            riskScore += 1;
        }

        // ROIC Analysis
        if (stock.roic && stock.roic < 0) {
            reasons.push(`ROIC negativo (${stock.roic.toFixed(1)}%)`);
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
        if (stock.dividend_yield && stock.dividend_yield > 5) {
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
        const shortCandidate = riskLevel === 'critical' || (stock.p_l && stock.p_l > 50) || (stock.roe && stock.roe < -10);

        return {
            riskLevel,
            reasons: reasons.slice(0, 3),
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
                    bgColor: 'bg-red-500/20',
                    borderColor: 'border-red-500/30',
                    gradient: 'from-red-600 to-red-800'
                };
            case 'high':
                return {
                    icon: AlertTriangle,
                    label: 'Alto',
                    color: 'text-orange-500',
                    bgColor: 'bg-orange-500/20',
                    borderColor: 'border-orange-500/30',
                    gradient: 'from-orange-600 to-orange-800'
                };
            case 'medium':
                return {
                    icon: Activity,
                    label: 'Médio',
                    color: 'text-yellow-500',
                    bgColor: 'bg-yellow-500/20',
                    borderColor: 'border-yellow-500/30',
                    gradient: 'from-yellow-600 to-yellow-800'
                };
        }
    };

    return (
        <div className="mb-8">
            {/* Header */}
            <div className="mb-6">
                <div className="flex items-center gap-4 mb-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-red-600 to-orange-600 flex items-center justify-center shadow-lg shadow-red-500/20">
                        <Skull className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <h2 className="text-2xl font-bold text-white">Ações Tóxicas</h2>
                        <p className="text-white/50">Ativos com indicadores de alerta</p>
                    </div>
                </div>

                {/* Filter Buttons */}
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
                                    <p className="text-xs text-white/50">{config.description}</p>
                                    <span className={`text-sm font-bold ${config.color}`}>
                                        {count}
                                    </span>
                                </div>
                            </motion.button>
                        );
                    })}
                </div>
            </div>

            {/* Results count */}
            <div className="mb-4 text-sm text-white/50">
                Mostrando {filteredStocks.length} {activeFilter !== 'all' && `de ${analyzedStocks.length}`} ações
            </div>

            {/* Toxic Stocks Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredStocks.map(({ stock, analysis }, index) => {
                    const riskConfig = getRiskConfig(analysis.riskLevel);
                    const RiskIcon = riskConfig.icon;

                    return (
                        <motion.div
                            key={stock.papel}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.05 }}
                            className={`relative rounded-xl border ${riskConfig.borderColor} bg-gradient-to-br from-slate-800/80 to-slate-900/90 overflow-hidden cursor-pointer group hover:scale-[1.01] transition-transform`}
                            onClick={() => onSelectStock(stock)}
                        >
                            {/* Risk Level Bar */}
                            <div className={`h-1 bg-gradient-to-r ${riskConfig.gradient}`} />

                            <div className="p-4">
                                <div className="flex items-start justify-between mb-3">
                                    {/* Stock Info */}
                                    <div className="flex items-center gap-3">
                                        <div className={`w-10 h-10 rounded-lg ${riskConfig.bgColor} flex items-center justify-center`}>
                                            <Flame className={`w-5 h-5 ${riskConfig.color}`} />
                                        </div>
                                        <div>
                                            <h3 className="font-bold text-white text-lg">{stock.papel}</h3>
                                            <p className="text-white/40 text-sm">{stock.setor || 'N/A'}</p>
                                        </div>
                                    </div>

                                    {/* Badges */}
                                    <div className="flex gap-1">
                                        <div className={`flex items-center gap-1 px-2 py-1 rounded-lg ${riskConfig.bgColor}`}>
                                            <RiskIcon className={`w-4 h-4 ${riskConfig.color}`} />
                                            <span className={`text-xs font-bold ${riskConfig.color}`}>{riskConfig.label}</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Key Metrics */}
                                <div className="grid grid-cols-4 gap-2 mb-3">
                                    <div className="text-center p-2 rounded-lg bg-white/5">
                                        <p className="text-white/40 text-xs">Cotação</p>
                                        <p className="text-white font-medium">R$ {stock.cotacao?.toFixed(2) || '0'}</p>
                                    </div>
                                    <div className="text-center p-2 rounded-lg bg-white/5">
                                        <p className="text-white/40 text-xs">P/L</p>
                                        <p className={`font-medium ${stock.p_l && stock.p_l < 0 ? 'text-red-400' : 'text-white'}`}>
                                            {stock.p_l?.toFixed(1) || '0'}x
                                        </p>
                                    </div>
                                    <div className="text-center p-2 rounded-lg bg-white/5">
                                        <p className="text-white/40 text-xs">ROE</p>
                                        <p className={`font-medium ${stock.roe && stock.roe < 0 ? 'text-red-400' : 'text-white'}`}>
                                            {stock.roe?.toFixed(1) || '0'}%
                                        </p>
                                    </div>
                                    <div className="text-center p-2 rounded-lg bg-white/5">
                                        <p className="text-white/40 text-xs">Score</p>
                                        <p className="text-orange-400 font-medium">{stock.super_score?.toFixed(1) || '0'}</p>
                                    </div>
                                </div>

                                {/* Alert Reasons */}
                                <div className="space-y-1 mb-3">
                                    {analysis.reasons.map((reason, i) => (
                                        <div key={i} className="flex items-center gap-2 text-sm">
                                            <AlertTriangle className={`w-3 h-3 ${riskConfig.color} flex-shrink-0`} />
                                            <span className="text-white/70">{reason}</span>
                                        </div>
                                    ))}
                                </div>

                                {/* Tags */}
                                <div className="flex flex-wrap gap-2">
                                    {analysis.turnaroundPotential && (
                                        <div className="flex items-center gap-1 px-2 py-1 rounded bg-cyan-500/20 border border-cyan-500/30">
                                            <RefreshCw className="w-3 h-3 text-cyan-400" />
                                            <span className="text-xs text-cyan-400 font-medium">Turnaround</span>
                                        </div>
                                    )}
                                    {analysis.shortCandidate && (
                                        <div className="flex items-center gap-1 px-2 py-1 rounded bg-purple-500/20 border border-purple-500/30">
                                            <TrendingDown className="w-3 h-3 text-purple-400" />
                                            <span className="text-xs text-purple-400 font-medium">Short</span>
                                        </div>
                                    )}
                                </div>

                                {/* View Details CTA */}
                                <div className="mt-3 flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity">
                                    <span className="text-xs text-white/40">Clique para análise completa</span>
                                    <ChevronRight className="w-4 h-4 text-white/40" />
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

            {/* Disclaimer */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="mt-6 p-4 rounded-xl bg-white/5 border border-white/10"
            >
                <div className="flex items-start gap-3">
                    <Eye className="w-5 h-5 text-white/40 flex-shrink-0 mt-0.5" />
                    <div>
                        <p className="text-sm text-white/60">
                            <span className="font-medium text-white/80">Lembre-se:</span> Ações com indicadores ruins podem estar em momentos
                            de crise temporária. Algumas se recuperam e geram retornos extraordinários. Faça sua própria análise antes de
                            qualquer decisão de investimento.
                        </p>
                    </div>
                </div>
            </motion.div>
        </div>
    );
}
