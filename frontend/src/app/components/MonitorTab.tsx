'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Shield, AlertTriangle, CheckCircle, RefreshCw, TrendingUp, TrendingDown, ArrowRight } from 'lucide-react';
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

    const runMonitor = async () => {
        setChecking(true);
        setError(null);
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${API_URL}/portfolio/monitor`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                setAlerts(data);
            } else {
                setError('Falha ao carregar dados de monitoramento.');
            }
        } catch (e) {
            console.error(e);
            setError('Erro de conexão.');
        } finally {
            setChecking(false);
            setLoading(false);
        }
    };

    useEffect(() => {
        runMonitor();
    }, []);

    if (loading && !alerts) {
        return (
            <div className="flex justify-center p-12">
                <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
            </div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
        >
            {/* Header */}
            <div className="bg-slate-800/60 border border-white/10 rounded-xl p-6 flex flex-col md:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-blue-500/20 rounded-xl">
                        <Shield className="w-8 h-8 text-blue-400" />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-white">Painel de Gestão</h2>
                        <p className="text-white/60 text-sm">
                            {alerts?.summary ?
                                `Monitorando ${alerts.portfolio_assets?.length || 0} ativos da Carteira Oficial (${alerts.summary.snapshot_date})` :
                                'Sistema de verificação de riscos'}
                        </p>
                    </div>
                </div>

                <button
                    onClick={runMonitor}
                    disabled={checking}
                    className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-white transition-colors disabled:opacity-50 text-sm font-medium"
                >
                    <RefreshCw className={`w-4 h-4 ${checking ? 'animate-spin' : ''}`} />
                    Atualizar Cotações
                </button>
            </div>

            {error && (
                <div className="p-4 bg-red-500/20 border border-red-500/50 rounded-xl text-red-300 flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5" />
                    {error}
                </div>
            )}

            {/* ALERTS SECTION - Only show if there are actual problems */}
            {(alerts?.stop_loss?.length || 0) > 0 || (alerts?.red_flags?.length || 0) > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* STOP LOSS ALERT */}
                    {(alerts?.stop_loss?.length || 0) > 0 && (
                        <div className="p-5 rounded-xl border bg-red-500/10 border-red-500/30">
                            <h3 className="flex items-center gap-2 text-lg font-bold text-red-400 mb-4">
                                <AlertTriangle className="w-5 h-5" />
                                Stop Loss Acionado
                            </h3>
                            <div className="space-y-2">
                                {alerts?.stop_loss.map((alarm: any) => (
                                    <div key={alarm.ticker} className="flex justify-between items-center bg-slate-900/80 p-3 rounded border border-red-500/20">
                                        <span className="font-bold text-white">{alarm.ticker}</span>
                                        <span className="font-bold text-red-400">{alarm.pnl_pct}%</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* RED FLAGS ALERT */}
                    {(alerts?.red_flags?.length || 0) > 0 && (
                        <div className="p-5 rounded-xl border bg-yellow-500/10 border-yellow-500/30">
                            <h3 className="flex items-center gap-2 text-lg font-bold text-yellow-400 mb-4">
                                <AlertTriangle className="w-5 h-5" />
                                Deterioração de Fundamentos
                            </h3>
                            <div className="space-y-2">
                                {alerts?.red_flags.map((alarm: any) => (
                                    <div key={alarm.ticker} className="flex flex-col bg-slate-900/80 p-3 rounded border border-yellow-500/20">
                                        <span className="font-bold text-white mb-1">{alarm.ticker}</span>
                                        <div className="flex flex-wrap gap-1">
                                            {alarm.new_flags.map((flag: string) => (
                                                <span key={flag} className="text-[10px] uppercase px-1.5 py-0.5 bg-yellow-500/20 text-yellow-200 rounded">
                                                    {flag}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            ) : null}

            {/* PORTFOLIO ASSETS TABLE */}
            <div>
                <h3 className="text-lg font-semibold text-white mb-4 pl-1 border-l-4 border-cyan-500 flex items-center gap-2">
                    <span className="pl-2">Carteira Recomendada</span>
                    <span className="text-xs font-normal text-white/40 bg-white/5 px-2 py-0.5 rounded-full">
                        Em tempo real
                    </span>
                </h3>

                <div className="overflow-x-auto rounded-xl border border-white/10 bg-slate-900/40 backdrop-blur-sm">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-white/5 border-b border-white/10 text-white/60">
                            <tr>
                                <th className="p-4 font-medium w-16 text-center">Rank</th>
                                <th className="p-4 font-medium">Ativo</th>
                                <th className="p-4 font-medium hidden md:table-cell">Setor</th>
                                <th className="p-4 font-medium text-right">Entrada</th>
                                <th className="p-4 font-medium text-right">Atual</th>
                                <th className="p-4 font-medium text-right">Resultado</th>
                                <th className="p-4 font-medium text-center">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {alerts?.portfolio_assets?.map((asset) => (
                                <tr
                                    key={asset.ticker}
                                    onClick={() => setSelectedTicker(asset.ticker)}
                                    className="hover:bg-white/5 transition-colors cursor-pointer"
                                >
                                    <td className="p-4 text-center text-white/40 font-mono">#{asset.rank}</td>
                                    <td className="p-4 font-bold text-white text-base">{asset.ticker}</td>
                                    <td className="p-4 text-white/60 hidden md:table-cell truncate max-w-[150px]">{asset.sector}</td>
                                    <td className="p-4 text-right text-white/60 font-mono">R$ {asset.entry_price.toFixed(2)}</td>
                                    <td className="p-4 text-right font-bold text-white font-mono">
                                        R$ {asset.current_price.toFixed(2)}
                                    </td>
                                    <td className="p-4 text-right">
                                        <div className={`inline-flex items-center gap-1 font-bold ${asset.pnl_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                            {asset.pnl_pct > 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                                            {asset.pnl_pct > 0 ? '+' : ''}{asset.pnl_pct.toFixed(2)}%
                                        </div>
                                    </td>
                                    <td className="p-4 text-center">
                                        <StatusBadge status={asset.status} />
                                    </td>
                                </tr>
                            ))}

                            {(!alerts?.portfolio_assets || alerts.portfolio_assets.length === 0) && (
                                <tr>
                                    <td colSpan={7} className="p-8 text-center text-white/30">
                                        Nenhum dado de carteira disponível para este snapshot.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Modal de Detalhes */}
            {
                selectedTicker && (
                    <StockDetailModal
                        ticker={selectedTicker}
                        isOpen={true}
                        onClose={() => setSelectedTicker(null)}
                    />
                )
            }
        </motion.div >
    );
}

function StatusBadge({ status }: { status: string }) {
    if (status === 'STOP LOSS') {
        return <span className="px-2 py-1 rounded bg-red-500/20 text-red-400 text-xs font-bold border border-red-500/30">STOP</span>;
    }
    if (status === 'ALERTA') {
        return <span className="px-2 py-1 rounded bg-yellow-500/20 text-yellow-400 text-xs font-bold border border-yellow-500/30">RISCO</span>;
    }
    if (status === 'SEM DADOS') {
        return <span className="px-2 py-1 rounded bg-slate-700 text-slate-400 text-xs font-bold">N/A</span>;
    }
    return <span className="px-2 py-1 rounded bg-green-500/20 text-green-400 text-xs font-bold border border-green-500/30">OK</span>;
}
