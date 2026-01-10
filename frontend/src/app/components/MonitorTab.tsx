'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
    Shield,
    Activity,
    TrendingUp,
    TrendingDown,
    AlertTriangle,
    RefreshCw,
    Target,
    ChevronRight,
    Search,
    Clock,
    BarChart3
} from 'lucide-react';
import StatCard from './StatCard';
import PremiumStockModal from './PremiumStockModal';
import { useDataCache } from '../contexts/DataCacheContext';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

interface Asset {
    rank: number;
    ticker: string;
    sector: string;
    entry_price: number;
    current_price: number;
    pnl_pct: number;
    current_score: number;
    status: string;
}

interface MonitorData {
    stop_loss: any[];
    red_flags: any[];
    portfolio_assets: Asset[];
    summary: {
        checked_assets: number;
        total_snapshot_assets: number;
        snapshot_date: string;
        data_source: string;
        avg_pnl: number;
        best_performer: { ticker: string; pnl: number };
        worst_performer: { ticker: string; pnl: number };
        coverage_pct: number;
        positive_breadth: number;
        negative_breadth: number;
    };
}

export default function MonitorTab() {
    const [data, setData] = useState<MonitorData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
    const { getCachedData, setCachedData } = useDataCache();

    const fetchMonitorData = async () => {
        const cacheKey = 'monitor_data';
        const cached = getCachedData(cacheKey);
        if (cached) {
            setData(cached);
            setLoading(false);
            return;
        }

        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${API_URL}/portfolio/monitor`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const monitorData = await response.json();
                setCachedData(cacheKey, monitorData);
                setData(monitorData);
            } else {
                setError('Falha ao carregar dados do monitor.');
            }
        } catch (e) {
            console.error(e);
            setError('Erro de conexão ao monitor.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMonitorData();
    }, []);

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center py-24 gap-4">
                <div className="relative">
                    <div className="w-16 h-16 rounded-full border-4 border-slate-700 border-t-cyan-500 animate-spin" />
                    <Shield className="w-6 h-6 text-cyan-400 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                </div>
                <p className="text-slate-400 text-sm">Atualizando monitor...</p>
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="p-8 text-center bg-red-500/10 border border-red-500/20 rounded-xl">
                <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                <p className="text-red-400 font-bold mb-2">Erro no Monitor</p>
                <p className="text-red-400/70 text-sm mb-4">{error || 'Dados indisponíveis'}</p>
                <button
                    onClick={fetchMonitorData}
                    className="px-6 py-2 bg-red-500 text-white rounded-lg font-bold hover:bg-red-600 transition-colors"
                >
                    Tentar Novamente
                </button>
            </div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
        >
            {/* Header section with context */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-white mb-1">Carteira Monitorada</h2>
                    <p className="text-xs text-slate-500 flex items-center gap-1.5 uppercase tracking-wider font-semibold">
                        <Clock className="w-3.5 h-3.5" /> Acompanhamento vs Snapshot de {data.summary.snapshot_date}
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/50 text-[10px] font-bold text-slate-400 flex items-center gap-2">
                        <Activity className="w-3.5 h-3.5 text-cyan-400" />
                        FONTE: {data.summary.data_source}
                    </div>
                    <button
                        onClick={fetchMonitorData}
                        className="p-2.5 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 rounded-xl border border-cyan-500/20 transition-all flex items-center gap-2 group"
                    >
                        <RefreshCw className="w-4 h-4 group-hover:rotate-180 transition-transform duration-500" />
                        <span className="text-xs font-bold uppercase tracking-wider px-1">Atualizar</span>
                    </button>
                </div>
            </div>

            {/* Standardized Rigid Stats Grid */}
            <div className="dashboard-stats-grid">
                <StatCard
                    title="Cobertura Ativa"
                    value={`${data.summary.coverage_pct}%`}
                    subtitle={`${data.summary.checked_assets}/${data.summary.total_snapshot_assets} Ativos`}
                    icon={Target}
                    gradient="from-blue-500 to-indigo-600"
                    tooltip="Percentual da carteira oficial sendo monitorado em tempo real."
                />
                <StatCard
                    title="Performance Live"
                    value={`${data.summary.avg_pnl > 0 ? '+' : ''}${data.summary.avg_pnl}%`}
                    subtitle="P/L Médio vs Snapshot"
                    icon={Activity}
                    gradient={data.summary.avg_pnl >= 0 ? "from-emerald-400 to-teal-600" : "from-red-400 to-rose-600"}
                    valueColor={data.summary.avg_pnl >= 0 ? "text-emerald-400" : "text-red-400"}
                    tooltip="Rentabilidade média dos ativos monitorados desde o último snapshot semanal."
                />
                <StatCard
                    title="Moveres do Dia"
                    value={data.summary.best_performer.ticker}
                    subtitle={`Alta de ${data.summary.best_performer.pnl}%`}
                    icon={TrendingUp}
                    gradient="from-green-400 to-emerald-600"
                    tooltip="Melhor performance individual detectada na sessão atual."
                />
                <StatCard
                    title="Alertas Ativos"
                    value={data.stop_loss.length + data.red_flags.length}
                    subtitle={`${data.stop_loss.length} Stop Loss | ${data.red_flags.length} Flags`}
                    icon={AlertTriangle}
                    gradient="from-orange-400 to-amber-600"
                    valueColor={data.stop_loss.length > 0 ? "text-red-400" : "text-amber-400"}
                    tooltip="Quantidade de ativos que atingiram critérios de saída ou novos riscos."
                />
            </div>

            {/* Assets Table */}
            <div className="bg-slate-900/40 rounded-2xl border border-white/5 overflow-hidden backdrop-blur-sm">
                <div className="px-6 py-4 border-b border-white/5 bg-white/[0.02] flex items-center justify-between">
                    <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                        <BarChart3 className="w-4 h-4 text-cyan-400" /> Ativos Sob Monitoramento
                    </h3>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-white/5 bg-white/[0.01]">
                                <th className="px-6 py-4 text-[10px] font-bold text-white/30 uppercase tracking-widest">Rank</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-white/30 uppercase tracking-widest">Ativo</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-white/30 uppercase tracking-widest">Preço Snapshot</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-white/30 uppercase tracking-widest">Preço Atual</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-white/30 uppercase tracking-widest">P/L %</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-white/30 uppercase tracking-widest">Super Score</th>
                                <th className="px-6 py-4 text-[10px] font-bold text-white/30 uppercase tracking-widest text-right">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {data.portfolio_assets.map((asset) => (
                                <tr
                                    key={asset.ticker}
                                    onClick={() => setSelectedTicker(asset.ticker)}
                                    className="group hover:bg-white/[0.02] transition-colors cursor-pointer"
                                >
                                    <td className="px-6 py-4">
                                        <span className="text-xs font-mono text-white/40 group-hover:text-white/60 transition-colors">
                                            #{asset.rank}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div>
                                            <p className="text-sm font-bold text-white group-hover:text-cyan-400 transition-colors">
                                                {asset.ticker}
                                            </p>
                                            <p className="text-[10px] text-white/20 uppercase font-bold tracking-tight">
                                                {asset.sector}
                                            </p>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-sm font-medium text-white/60">
                                        R$ {asset.entry_price.toFixed(2)}
                                    </td>
                                    <td className="px-6 py-4 text-sm font-bold text-white">
                                        R$ {asset.current_price.toFixed(2)}
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`text-sm font-black ${asset.pnl_pct >= 0 ? 'text-emerald-400' : 'text-rose-500'}`}>
                                            {asset.pnl_pct >= 0 ? '+' : ''}{asset.pnl_pct}%
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-2">
                                            <div className="w-16 h-1.5 rounded-full bg-white/5 overflow-hidden">
                                                <div
                                                    className="h-full bg-gradient-to-r from-cyan-500 to-blue-500"
                                                    style={{ width: `${asset.current_score}%` }}
                                                />
                                            </div>
                                            <span className="text-xs font-bold text-white/40">{asset.current_score}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <span className={`
                                            inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest
                                            ${asset.status === 'OK' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                                                asset.status === 'STOP LOSS' ? 'bg-red-500/10 text-red-500 border border-red-500/20' :
                                                    'bg-amber-500/10 text-amber-500 border border-amber-500/20'}
                                        `}>
                                            <span className={`w-1.5 h-1.5 rounded-full ${asset.status === 'OK' ? 'bg-emerald-400' : 'bg-red-500'}`} />
                                            {asset.status}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Premium Stock Modal */}
            {selectedTicker && (
                <PremiumStockModal
                    ticker={selectedTicker}
                    isOpen={true}
                    onClose={() => setSelectedTicker(null)}
                />
            )}
        </motion.div>
    );
}
