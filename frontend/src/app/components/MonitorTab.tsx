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
    summary: { snapshot_date: string; checked_assets: number };
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
            {/* Compact Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-xl font-semibold text-white">Carteira Monitorada</h2>
                    <p className="text-sm text-white/40">
                        {alerts?.summary?.snapshot_date ? `Snapshot: ${alerts.summary.snapshot_date}` : 'Carregando...'}
                    </p>
                </div>
                <div className="flex items-center gap-4">
                    {/* Mini Stats */}
                    <div className="flex items-center gap-6 text-sm">
                        <div className="text-center">
                            <div className="text-lg font-bold text-white">{alerts?.portfolio_assets?.length || 0}</div>
                            <div className="text-[10px] text-white/40 uppercase">Ativos</div>
                        </div>
                        <div className="text-center">
                            <div className="text-lg font-bold text-emerald-400">{okCount}</div>
                            <div className="text-[10px] text-white/40 uppercase">OK</div>
                        </div>
                        <div className="text-center">
                            <div className="text-lg font-bold text-amber-400">{alertCount}</div>
                            <div className="text-[10px] text-white/40 uppercase">Alertas</div>
                        </div>
                    </div>
                    <button
                        onClick={runMonitor}
                        disabled={checking}
                        className="flex items-center gap-2 px-4 py-2 bg-cyan-500 hover:bg-cyan-400 disabled:bg-cyan-500/50 rounded-lg text-white text-sm font-medium transition-colors"
                    >
                        <RefreshCw className={`w-4 h-4 ${checking ? 'animate-spin' : ''}`} />
                        Atualizar
                    </button>
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
