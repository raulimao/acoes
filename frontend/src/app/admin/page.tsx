'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
    Settings,
    Shield,
    Scale,
    FileText,
    Filter,
    Save,
    RefreshCw,
    AlertTriangle,
    CheckCircle,
    Loader2,
    ArrowLeft
} from 'lucide-react';
import Link from 'next/link';

interface RedFlagsConfig {
    div_trap_threshold: number;
    low_liq_threshold: number;
    high_debt_threshold: number;
    low_margin_threshold: number;
    stagnant_growth_threshold: number;
}

interface StrategyWeights {
    graham: number;
    greenblatt: number;
    bazin: number;
    qualidade: number;
}

interface ReportSettings {
    top_n_stocks: number;
    show_cyclical_warning: boolean;
    show_regulated_warning: boolean;
    show_stagnant_warning: boolean;
}

interface FilterSettings {
    dedup_enabled: boolean;
    liquidity_score_cap: number;
}

interface Config {
    red_flags: RedFlagsConfig;
    strategy_weights: StrategyWeights;
    report_settings: ReportSettings;
    filter_settings: FilterSettings;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://acoes.onrender.com';

export default function AdminPage() {
    const [config, setConfig] = useState<Config | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const fetchConfig = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const token = localStorage.getItem('token');

            if (!token) {
                setError('Você não está logado. Faça login primeiro.');
                return;
            }

            const response = await fetch(`${API_URL}/api/admin/config`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.status === 403) {
                const data = await response.json().catch(() => ({}));
                setError(`Acesso negado: ${data.detail || 'Você não tem permissão de administrador.'}`);
                return;
            }

            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.detail || `HTTP ${response.status}`);
            }

            const data = await response.json();
            setConfig(data);
        } catch (err: any) {
            console.error('Admin fetch error:', err);
            setError(`Erro: ${err.message || 'Verifique se você está logado como admin.'}`);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchConfig();
    }, [fetchConfig]);

    const saveSection = async (key: string, value: any) => {
        setSaving(true);
        setError(null);
        setSuccess(null);

        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${API_URL}/api/admin/config`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ key, value })
            });

            if (!response.ok) {
                throw new Error('Failed to save config');
            }

            setSuccess(`Seção "${key}" salva com sucesso!`);
            setTimeout(() => setSuccess(null), 3000);
        } catch (err) {
            setError('Erro ao salvar configurações.');
        } finally {
            setSaving(false);
        }
    };

    const updateRedFlags = (field: keyof RedFlagsConfig, value: number) => {
        if (!config) return;
        setConfig({
            ...config,
            red_flags: { ...config.red_flags, [field]: value }
        });
    };

    const updateStrategyWeight = (strategy: keyof StrategyWeights, value: number) => {
        if (!config) return;
        setConfig({
            ...config,
            strategy_weights: { ...config.strategy_weights, [strategy]: value }
        });
    };

    const updateReportSetting = (field: keyof ReportSettings, value: any) => {
        if (!config) return;
        setConfig({
            ...config,
            report_settings: { ...config.report_settings, [field]: value }
        });
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
            </div>
        );
    }

    if (error && !config) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
                <div className="bg-red-500/20 border border-red-500/50 rounded-xl p-6 max-w-md text-center">
                    <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                    <p className="text-red-300">{error}</p>
                    <Link href="/" className="mt-4 inline-block text-cyan-400 hover:underline">
                        ← Voltar ao Dashboard
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="flex items-center gap-4 mb-8">
                    <Link href="/" className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors">
                        <ArrowLeft className="w-5 h-5 text-white" />
                    </Link>
                    <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center">
                            <Settings className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold text-white">Painel de Administração</h1>
                            <p className="text-white/50">Configure os parâmetros do sistema</p>
                        </div>
                    </div>
                </div>

                {/* Alerts */}
                {error && (
                    <div className="mb-4 p-4 bg-red-500/20 border border-red-500/50 rounded-xl flex items-center gap-3">
                        <AlertTriangle className="w-5 h-5 text-red-400" />
                        <span className="text-red-300">{error}</span>
                    </div>
                )}

                {success && (
                    <div className="mb-4 p-4 bg-green-500/20 border border-green-500/50 rounded-xl flex items-center gap-3">
                        <CheckCircle className="w-5 h-5 text-green-400" />
                        <span className="text-green-300">{success}</span>
                    </div>
                )}

                {config && (
                    <div className="space-y-6">
                        {/* Red Flags Section */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="bg-slate-800/60 border border-white/10 rounded-xl p-6"
                        >
                            <div className="flex items-center justify-between mb-6">
                                <div className="flex items-center gap-3">
                                    <Shield className="w-6 h-6 text-red-400" />
                                    <h2 className="text-xl font-bold text-white">🚩 Red Flags</h2>
                                </div>
                                <button
                                    onClick={() => saveSection('red_flags', config.red_flags)}
                                    disabled={saving}
                                    className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg transition-colors disabled:opacity-50"
                                >
                                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                    Salvar
                                </button>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="text-white/70 text-sm">Dividend Trap (DY maior que)</label>
                                    <div className="flex items-center gap-2">
                                        <input
                                            type="number"
                                            step="0.01"
                                            value={config.red_flags.div_trap_threshold * 100}
                                            onChange={(e) => updateRedFlags('div_trap_threshold', parseFloat(e.target.value) / 100)}
                                            className="w-full px-4 py-2 bg-slate-700 border border-white/10 rounded-lg text-white"
                                        />
                                        <span className="text-white/50">%</span>
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <label className="text-white/70 text-sm">Baixa Liquidez (menor que)</label>
                                    <div className="flex items-center gap-2">
                                        <input
                                            type="number"
                                            value={config.red_flags.low_liq_threshold}
                                            onChange={(e) => updateRedFlags('low_liq_threshold', parseFloat(e.target.value))}
                                            className="w-full px-4 py-2 bg-slate-700 border border-white/10 rounded-lg text-white"
                                        />
                                        <span className="text-white/50">R$/dia</span>
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <label className="text-white/70 text-sm">Dívida Alta (maior que)</label>
                                    <div className="flex items-center gap-2">
                                        <input
                                            type="number"
                                            step="0.1"
                                            value={config.red_flags.high_debt_threshold}
                                            onChange={(e) => updateRedFlags('high_debt_threshold', parseFloat(e.target.value))}
                                            className="w-full px-4 py-2 bg-slate-700 border border-white/10 rounded-lg text-white"
                                        />
                                        <span className="text-white/50">x PL</span>
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <label className="text-white/70 text-sm">Margem Baixa (menor que)</label>
                                    <div className="flex items-center gap-2">
                                        <input
                                            type="number"
                                            step="0.01"
                                            value={config.red_flags.low_margin_threshold * 100}
                                            onChange={(e) => updateRedFlags('low_margin_threshold', parseFloat(e.target.value) / 100)}
                                            className="w-full px-4 py-2 bg-slate-700 border border-white/10 rounded-lg text-white"
                                        />
                                        <span className="text-white/50">%</span>
                                    </div>
                                </div>
                            </div>
                        </motion.div>

                        {/* Strategy Weights Section */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                            className="bg-slate-800/60 border border-white/10 rounded-xl p-6"
                        >
                            <div className="flex items-center justify-between mb-6">
                                <div className="flex items-center gap-3">
                                    <Scale className="w-6 h-6 text-yellow-400" />
                                    <h2 className="text-xl font-bold text-white">⚖️ Pesos das Estratégias</h2>
                                </div>
                                <button
                                    onClick={() => saveSection('strategy_weights', config.strategy_weights)}
                                    disabled={saving}
                                    className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg transition-colors disabled:opacity-50"
                                >
                                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                    Salvar
                                </button>
                            </div>

                            <div className="space-y-4">
                                {Object.entries(config.strategy_weights).map(([strategy, weight]) => (
                                    <div key={strategy} className="space-y-2">
                                        <div className="flex items-center justify-between">
                                            <label className="text-white capitalize">{strategy}</label>
                                            <span className="text-cyan-400 font-bold">{weight.toFixed(1)}</span>
                                        </div>
                                        <input
                                            type="range"
                                            min="0"
                                            max="3"
                                            step="0.1"
                                            value={weight}
                                            onChange={(e) => updateStrategyWeight(strategy as keyof StrategyWeights, parseFloat(e.target.value))}
                                            className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                                        />
                                    </div>
                                ))}
                            </div>
                        </motion.div>

                        {/* Report Settings Section */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                            className="bg-slate-800/60 border border-white/10 rounded-xl p-6"
                        >
                            <div className="flex items-center justify-between mb-6">
                                <div className="flex items-center gap-3">
                                    <FileText className="w-6 h-6 text-blue-400" />
                                    <h2 className="text-xl font-bold text-white">📄 Relatório PDF</h2>
                                </div>
                                <button
                                    onClick={() => saveSection('report_settings', config.report_settings)}
                                    disabled={saving}
                                    className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg transition-colors disabled:opacity-50"
                                >
                                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                    Salvar
                                </button>
                            </div>

                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <label className="text-white/70 text-sm">Top N Ações no Ranking</label>
                                    <input
                                        type="number"
                                        min="5"
                                        max="50"
                                        value={config.report_settings.top_n_stocks}
                                        onChange={(e) => updateReportSetting('top_n_stocks', parseInt(e.target.value))}
                                        className="w-full px-4 py-2 bg-slate-700 border border-white/10 rounded-lg text-white"
                                    />
                                </div>

                                <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                                    <span className="text-white">Mostrar avisos de setores cíclicos</span>
                                    <button
                                        onClick={() => updateReportSetting('show_cyclical_warning', !config.report_settings.show_cyclical_warning)}
                                        className={`w-12 h-6 rounded-full transition-colors ${config.report_settings.show_cyclical_warning ? 'bg-cyan-500' : 'bg-slate-600'}`}
                                    >
                                        <div className={`w-5 h-5 bg-white rounded-full transform transition-transform ${config.report_settings.show_cyclical_warning ? 'translate-x-6' : 'translate-x-1'}`} />
                                    </button>
                                </div>

                                <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                                    <span className="text-white">Mostrar avisos de setores regulados</span>
                                    <button
                                        onClick={() => updateReportSetting('show_regulated_warning', !config.report_settings.show_regulated_warning)}
                                        className={`w-12 h-6 rounded-full transition-colors ${config.report_settings.show_regulated_warning ? 'bg-cyan-500' : 'bg-slate-600'}`}
                                    >
                                        <div className={`w-5 h-5 bg-white rounded-full transform transition-transform ${config.report_settings.show_regulated_warning ? 'translate-x-6' : 'translate-x-1'}`} />
                                    </button>
                                </div>

                                <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                                    <span className="text-white">Mostrar avisos de empresas estagnadas</span>
                                    <button
                                        onClick={() => updateReportSetting('show_stagnant_warning', !config.report_settings.show_stagnant_warning)}
                                        className={`w-12 h-6 rounded-full transition-colors ${config.report_settings.show_stagnant_warning ? 'bg-cyan-500' : 'bg-slate-600'}`}
                                    >
                                        <div className={`w-5 h-5 bg-white rounded-full transform transition-transform ${config.report_settings.show_stagnant_warning ? 'translate-x-6' : 'translate-x-1'}`} />
                                    </button>
                                </div>
                            </div>
                        </motion.div>

                        {/* Actions */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.3 }}
                            className="flex gap-4"
                        >
                            <button
                                onClick={fetchConfig}
                                className="flex items-center gap-2 px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-xl transition-colors"
                            >
                                <RefreshCw className="w-5 h-5" />
                                Recarregar
                            </button>
                        </motion.div>
                    </div>
                )}
            </div>
        </div>
    );
}
