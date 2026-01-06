'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Shield, AlertTriangle, RefreshCw, TrendingUp, TrendingDown, ChevronDown, ChevronUp } from 'lucide-react';
import StockDetailModal from './StockDetailModal';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

interface AssetStatus {
    rank: number;
    ticker: string;
    sector: string;
    entry_price: number;
    current_price: number;
    pnl_pct: number;
    current_score: number;
    status: 'OK' | 'ALERTA' | 'STOP LOSS' | 'SEM DADOS';
}

interface MonitorAlerts {
    summary: {
        snapshot_date: string;
        checked_assets: number;
        total_snapshot_assets: number;
        avg_pnl: number;
        coverage_pct: number;
        positive_breadth: number;
        negative_breadth: number;
        best_performer: { ticker: string; pnl: number };
        worst_performer: { ticker: string; pnl: number };
    };
    stop_loss: Array<any>;
    red_flags: Array<any>;
    portfolio_assets: AssetStatus[];
}

export default function MonitorTab() {
    const [alerts, setAlerts] = useState<MonitorAlerts | null>(null);
    const [loading, setLoading] = useState(true);
    const [checking, setChecking] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
    const [showAlerts, setShowAlerts] = useState(false);

    const runMonitor = async () => {
        setChecking(true);
        setError(null);
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${API_URL}/portfolio/monitor`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                setAlerts(await response.json());
            } else {
                setError('Falha ao carregar dados.');
            }
        } catch (e) {
            setError('Erro de conexão.');
        } finally {
            setChecking(false);
            setLoading(false);
        }
    };

    useEffect(() => { runMonitor(); }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center p-20">
                <RefreshCw className="w-8 h-8 text-cyan-500 animate-spin" />
            </div>
        );
    }

    const alertCount = (alerts?.red_flags?.length || 0) + (alerts?.stop_loss?.length || 0);
    const okCount = alerts?.portfolio_assets?.filter(a => a.status === 'OK').length || 0;

    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
            {/* Expanded Header */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-white tracking-tight">Carteira Monitorada</h2>
                    <p className="text-sm text-white/40">
                        {alerts?.summary?.snapshot_date ? `Acompanhamento semanal baseado no Snapshot de ${alerts.summary.snapshot_date}` : 'Carregando...'}
                    </p>
                </div>
                <button
                    onClick={runMonitor}
                    disabled={checking}
                    className="flex items-center justify-center gap-2 px-6 py-2.5 bg-cyan-600 hover:bg-cyan-500 disabled:bg-cyan-600/50 rounded-xl text-white text-sm font-semibold transition-all shadow-lg shadow-cyan-900/20 active:scale-95"
                >
                    <RefreshCw className={`w-4 h-4 ${checking ? 'animate-spin' : ''}`} />
                    Atualizar Cotações Live
                </button>
            </div>

            {/* Strategic Stats Grid - Premium Redesign */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                {/* Coverage Card - Glassmorphism */}
                <div className="relative group overflow-hidden bg-gradient-to-br from-slate-900/80 to-slate-800/40 backdrop-blur-xl border border-white/10 rounded-2xl p-5 shadow-2xl transition-all hover:border-cyan-500/30">
                    <div className="absolute -right-2 -top-2 w-20 h-20 bg-cyan-500/5 rounded-full blur-2xl group-hover:bg-cyan-500/10 transition-colors" />
                    <div className="flex justify-between items-center mb-4">
                        <div className="flex items-center gap-2">
                            <div className="p-2 bg-cyan-500/10 rounded-lg">
                                <Shield className="w-4 h-4 text-cyan-400" />
                            </div>
                            <span className="text-[11px] font-bold text-white/40 tracking-[0.1em] uppercase">Cobertura Ativa</span>
                        </div>
                    </div>
                    <div className="flex items-end gap-2 mb-3">
                        <span className="text-4xl font-extrabold text-white tracking-tighter tabular-nums leading-none">
                            {alerts?.summary?.coverage_pct}%
                        </span>
                        <span className="text-xs font-medium text-white/20 mb-1 uppercase tracking-tight">do Portfólio</span>
                    </div>
                    <div className="relative h-2 w-full bg-white/5 rounded-full overflow-hidden">
                        <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${alerts?.summary?.coverage_pct}%` }}
                            transition={{ duration: 1, ease: "easeOut" }}
                            className="absolute top-0 left-0 h-full bg-gradient-to-r from-cyan-600 to-cyan-400 rounded-full shadow-[0_0_12px_rgba(34,211,238,0.3)]"
                        />
                    </div>
                    <div className="mt-3 flex items-center justify-between">
                        <span className="text-[10px] text-white/30 font-medium italic">
                            {alerts?.summary?.checked_assets} de {alerts?.summary?.total_snapshot_assets} ativos
                        </span>
                    </div>
                </div>

                {/* Avg PnL Card - Heat Style */}
                <div className="relative group overflow-hidden bg-gradient-to-br from-slate-900/80 to-slate-800/40 backdrop-blur-xl border border-white/10 rounded-2xl p-5 shadow-2xl transition-all hover:border-emerald-500/30">
                    <div className="absolute -right-2 -top-2 w-24 h-24 bg-emerald-500/5 rounded-full blur-2xl" />
                    <div className="flex justify-between items-center mb-4">
                        <div className="flex items-center gap-2">
                            <div className={`p-2 rounded-lg ${alerts?.summary?.avg_pnl && alerts.summary.avg_pnl >= 0 ? 'bg-emerald-500/10' : 'bg-red-500/10'}`}>
                                <TrendingUp className={`w-4 h-4 ${alerts?.summary?.avg_pnl && alerts.summary.avg_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`} />
                            </div>
                            <span className="text-[11px] font-bold text-white/40 tracking-[0.1em] uppercase">Performance Live</span>
                        </div>
                    </div>
                    <div className="flex flex-col gap-1">
                        <span className={`text-4xl font-extrabold tracking-tighter tabular-nums leading-none ${alerts?.summary?.avg_pnl && alerts.summary.avg_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            {alerts?.summary?.avg_pnl && alerts.summary.avg_pnl > 0 ? '+' : ''}{alerts?.summary?.avg_pnl}%
                        </span>
                        <div className="mt-4 flex items-center gap-2">
                            <div className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider ${alerts?.summary?.avg_pnl && alerts.summary.avg_pnl >= 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                                {alerts?.summary?.avg_pnl && alerts.summary.avg_pnl >= 0 ? 'Lucro Médio' : 'Prejuízo Médio'}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Breadth Card - Structural Style */}
                <div className="relative group overflow-hidden bg-gradient-to-br from-slate-900/80 to-slate-800/40 backdrop-blur-xl border border-white/10 rounded-2xl p-5 shadow-2xl transition-all hover:border-amber-500/30">
                    <div className="flex justify-between items-center mb-5">
                        <span className="text-[11px] font-bold text-white/40 tracking-[0.1em] uppercase">Sentimento da Carteira</span>
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                        <div className="flex flex-col">
                            <span className="text-2xl font-bold text-emerald-400 tabular-nums">{alerts?.summary?.positive_breadth}</span>
                            <span className="text-[9px] font-bold text-white/30 uppercase tracking-tighter">Verdes</span>
                        </div>
                        <div className="flex flex-col border-x border-white/5 px-2">
                            <span className="text-2xl font-bold text-red-400 tabular-nums">{alerts?.summary?.negative_breadth}</span>
                            <span className="text-[9px] font-bold text-white/30 uppercase tracking-tighter">Vermelhas</span>
                        </div>
                        <div className="flex flex-col pl-2">
                            <span className="text-2xl font-bold text-amber-400 tabular-nums">{alertCount}</span>
                            <span className="text-[9px] font-bold text-white/30 uppercase tracking-tighter">Riscos</span>
                        </div>
                    </div>
                    <div className="mt-5 flex gap-1 h-1.5 rounded-full overflow-hidden w-full opacity-60">
                        <div
                            className="bg-emerald-500 h-full transition-all duration-700"
                            style={{ width: `${(alerts?.summary?.positive_breadth || 0) / (alerts?.summary?.checked_assets || 1) * 100}%` }}
                        />
                        <div
                            className="bg-red-500 h-full transition-all duration-700"
                            style={{ width: `${(alerts?.summary?.negative_breadth || 0) / (alerts?.summary?.checked_assets || 1) * 100}%` }}
                        />
                    </div>
                </div>

                {/* Leaderboard Card - Ranking Style */}
                <div className="relative group overflow-hidden bg-gradient-to-br from-slate-900/80 to-slate-800/40 backdrop-blur-xl border border-white/10 rounded-2xl p-5 shadow-2xl transition-all hover:border-purple-500/30">
                    <div className="flex justify-between items-center mb-4">
                        <span className="text-[11px] font-bold text-white/40 tracking-[0.1em] uppercase">Moveres do Dia</span>
                    </div>
                    <div className="space-y-3">
                        <div
                            className="flex items-center justify-between group/item cursor-pointer"
                            onClick={() => alerts?.summary?.best_performer?.ticker && setSelectedTicker(alerts.summary.best_performer.ticker)}
                        >
                            <div className="flex items-center gap-2">
                                <div className="w-1.5 h-6 bg-emerald-500/50 rounded-full group-hover/item:bg-emerald-400 transition-colors" />
                                <div>
                                    <div className="text-[10px] text-white/30 font-bold uppercase tracking-tight leading-none mb-1">Destaque Alta</div>
                                    <div className="text-sm font-bold text-white">{alerts?.summary?.best_performer?.ticker}</div>
                                </div>
                            </div>
                            <div className="text-right">
                                <span className="text-sm font-black italic text-emerald-400">+{alerts?.summary?.best_performer?.pnl}%</span>
                            </div>
                        </div>
                        <div
                            className="flex items-center justify-between group/item cursor-pointer"
                            onClick={() => alerts?.summary?.worst_performer?.ticker && setSelectedTicker(alerts.summary.worst_performer.ticker)}
                        >
                            <div className="flex items-center gap-2">
                                <div className="w-1.5 h-6 bg-red-500/50 rounded-full group-hover/item:bg-red-400 transition-colors" />
                                <div>
                                    <div className="text-[10px] text-white/30 font-bold uppercase tracking-tight leading-none mb-1">Destaque Baixa</div>
                                    <div className="text-sm font-bold text-white">{alerts?.summary?.worst_performer?.ticker}</div>
                                </div>
                            </div>
                            <div className="text-right">
                                <span className="text-sm font-black italic text-red-400">{alerts?.summary?.worst_performer?.pnl}%</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {error && (
                <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4" /> {error}
                </div>
            )}

            {/* Collapsible Alerts Summary */}
            {alertCount > 0 && (
                <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl overflow-hidden">
                    <button
                        onClick={() => setShowAlerts(!showAlerts)}
                        className="w-full flex items-center justify-between p-4 text-left hover:bg-amber-500/5 transition-colors"
                    >
                        <div className="flex items-center gap-3">
                            <AlertTriangle className="w-5 h-5 text-amber-400" />
                            <span className="font-medium text-amber-400">
                                {alertCount} {alertCount === 1 ? 'alerta detectado' : 'alertas detectados'}
                            </span>
                        </div>
                        {showAlerts ? (
                            <ChevronUp className="w-5 h-5 text-amber-400" />
                        ) : (
                            <ChevronDown className="w-5 h-5 text-amber-400" />
                        )}
                    </button>

                    {showAlerts && (
                        <div className="px-4 pb-4 space-y-3">
                            {/* Stop Losses */}
                            {alerts?.stop_loss?.map((alarm: any) => (
                                <div key={alarm.ticker} className="flex items-center justify-between p-3 bg-red-500/10 rounded-lg border border-red-500/20">
                                    <div className="flex items-center gap-2">
                                        <span className="w-2 h-2 rounded-full bg-red-500" />
                                        <span className="font-medium text-white">{alarm.ticker}</span>
                                        <span className="text-xs text-red-400 bg-red-500/20 px-2 py-0.5 rounded">STOP LOSS</span>
                                    </div>
                                    <span className="font-bold text-red-400">{alarm.pnl_pct?.toFixed(1)}%</span>
                                </div>
                            ))}

                            {/* Red Flags */}
                            {alerts?.red_flags?.map((alarm: any) => (
                                <div key={alarm.ticker} className="flex items-center justify-between p-3 bg-amber-500/5 rounded-lg border border-amber-500/10">
                                    <div className="flex items-center gap-2">
                                        <span className="w-2 h-2 rounded-full bg-amber-500" />
                                        <span className="font-medium text-white">{alarm.ticker}</span>
                                    </div>
                                    <div className="flex gap-1">
                                        {alarm.new_flags?.slice(0, 2).map((f: string) => (
                                            <span key={f} className="text-[10px] text-amber-300 bg-amber-500/20 px-1.5 py-0.5 rounded">
                                                {f.replace('_', ' ')}
                                            </span>
                                        ))}
                                        {alarm.new_flags?.length > 2 && (
                                            <span className="text-[10px] text-amber-300/60">+{alarm.new_flags.length - 2}</span>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Clean Table */}
            <div className="rounded-xl border border-white/10 overflow-hidden bg-slate-900/50">
                <table className="w-full">
                    <thead>
                        <tr className="border-b border-white/10 text-xs text-white/40 uppercase tracking-wider">
                            <th className="text-left p-4 w-12">#</th>
                            <th className="text-left p-4">Ativo</th>
                            <th className="text-left p-4 hidden md:table-cell">Setor</th>
                            <th className="text-right p-4">Entrada</th>
                            <th className="text-right p-4">Atual</th>
                            <th className="text-right p-4">Var.</th>
                            <th className="text-center p-4 w-20">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {alerts?.portfolio_assets?.map((asset) => (
                            <tr
                                key={asset.ticker}
                                onClick={() => setSelectedTicker(asset.ticker)}
                                className="border-b border-white/5 hover:bg-white/5 cursor-pointer transition-colors"
                            >
                                <td className="p-4 text-white/30 text-sm">{asset.rank}</td>
                                <td className="p-4 font-semibold text-white">{asset.ticker}</td>
                                <td className="p-4 text-white/50 text-sm hidden md:table-cell truncate max-w-[200px]">
                                    {asset.sector}
                                </td>
                                <td className="p-4 text-right text-white/40 text-sm font-mono">
                                    R$ {asset.entry_price?.toFixed(2)}
                                </td>
                                <td className="p-4 text-right text-white font-mono">
                                    R$ {asset.current_price?.toFixed(2)}
                                </td>
                                <td className="p-4 text-right">
                                    <span className={`font-medium ${asset.pnl_pct >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                        {asset.pnl_pct > 0 ? '+' : ''}{asset.pnl_pct?.toFixed(2)}%
                                    </span>
                                </td>
                                <td className="p-4 text-center">
                                    <StatusDot status={asset.status} />
                                </td>
                            </tr>
                        ))}
                        {!alerts?.portfolio_assets?.length && (
                            <tr>
                                <td colSpan={7} className="p-8 text-center text-white/30">
                                    Nenhum ativo monitorado.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {selectedTicker && (
                <StockDetailModal
                    ticker={selectedTicker}
                    isOpen={true}
                    onClose={() => setSelectedTicker(null)}
                />
            )}
        </motion.div>
    );
}

function StatusDot({ status }: { status: string }) {
    const colors: Record<string, string> = {
        'OK': 'bg-emerald-500',
        'ALERTA': 'bg-amber-500',
        'STOP LOSS': 'bg-red-500',
        'SEM DADOS': 'bg-slate-500',
    };
    return (
        <div className="flex items-center justify-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${colors[status] || colors['OK']}`} />
            <span className="text-xs text-white/50 hidden sm:inline">
                {status === 'STOP LOSS' ? 'STOP' : status === 'ALERTA' ? 'RISCO' : status}
            </span>
        </div>
    );
}
