'use client';
import { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { Lock } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

interface Alert {
    type: 'success' | 'warning' | 'info';
    icon: string;
    title: string;
    message: string;
}

export default function EngagementWidgets() {
    const { user } = useAuth();
    const router = useRouter();
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState(true);
    const [downloadError, setDownloadError] = useState<string | null>(null);

    useEffect(() => {
        fetchAlerts();
    }, []);

    const fetchAlerts = async () => {
        try {
            const response = await axios.get(`${API_URL}/alerts`);
            setAlerts(response.data.alerts);
        } catch (error) {
            console.error('Error fetching alerts:', error);
        } finally {
            setLoading(false);
        }
    };

    const downloadReport = async () => {
        if (!user?.is_premium) {
            router.push('/pricing');
            return;
        }

        try {
            setLoading(true);
            setDownloadError(null);
            const token = localStorage.getItem('token');
            const response = await axios.get(`${API_URL}/reports/weekly`, {
                headers: { Authorization: `Bearer ${token}` },
                responseType: 'blob', // Important: response as binary data
            });

            // Create blob link to download
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', 'relatorio_semanal.pdf');
            document.body.appendChild(link);
            link.click();
            link.parentNode?.removeChild(link);
        } catch (error) {
            console.error('Error downloading report:', error);
            setDownloadError("Erro ao baixar. Tente novamente.");
            // Clear error after 3 seconds
            setTimeout(() => setDownloadError(null), 3000);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return null;

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {/* Alerts Widget */}
            <div className="md:col-span-2 bg-gray-800 rounded-xl p-6 border border-gray-700">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold text-white flex items-center gap-2">
                        🔔 Insights da Semana
                    </h3>
                    <span className="bg-blue-900 text-blue-200 text-xs px-2 py-1 rounded-full">
                        Novidades
                    </span>
                </div>

                <div className="space-y-3">
                    {alerts.length === 0 ? (
                        <p className="text-gray-400">Nenhum alerta importante esta semana.</p>
                    ) : (
                        alerts.map((alert, index) => (
                            <motion.div
                                key={index}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: index * 0.1 }}
                                className={`p-4 rounded-lg border flex items-start gap-4 ${alert.type === 'success'
                                    ? 'bg-green-900/20 border-green-800'
                                    : alert.type === 'warning'
                                        ? 'bg-red-900/20 border-red-800'
                                        : 'bg-blue-900/20 border-blue-800'
                                    }`}
                            >
                                <div className="text-2xl">{alert.icon}</div>
                                <div>
                                    <h4 className={`font-bold ${alert.type === 'success' ? 'text-green-400' :
                                        alert.type === 'warning' ? 'text-red-400' : 'text-blue-400'
                                        }`}>
                                        {alert.title}
                                    </h4>
                                    <p className="text-gray-300 text-sm mt-1">{alert.message}</p>
                                </div>
                            </motion.div>
                        ))
                    )}
                </div>
            </div>

            {/* Weekly Report Widget (Market Intelligence Style) */}
            <div className={`relative rounded-xl p-6 border flex flex-col justify-between overflow-hidden group ${user?.is_premium
                ? 'bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 border-purple-500/50 shadow-lg shadow-purple-900/20'
                : 'bg-gray-900 border-gray-700 opacity-90'
                }`}>

                {/* Decorative Background Elements */}
                {user?.is_premium && (
                    <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/10 rounded-full blur-3xl -mr-16 -mt-16 transition-all group-hover:bg-purple-500/20" />
                )}

                <div>
                    <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                            <span className="bg-amber-900/30 text-amber-200 border border-amber-500/30 text-[10px] uppercase tracking-wider font-bold px-2 py-1 rounded-full">
                                Market Intelligence
                            </span>
                        </div>
                        {!user?.is_premium && <Lock className="w-5 h-5 text-gray-500" />}
                    </div>

                    <h3 className="text-xl font-bold text-white mb-2 leading-tight">
                        Relatório de Mercado <span className="text-purple-400">Semanal</span>
                    </h3>

                    <p className="text-gray-300 text-sm mb-6 leading-relaxed">
                        Acesse análises exclusivas, gráficos de valuation setorial e o Top 10 Ações segundo nosso algoritmo.
                    </p>
                </div>

                <div className="space-y-2">
                    <button
                        onClick={user?.is_premium ? downloadReport : () => router.push('/pricing')}
                        disabled={loading}
                        className={`w-full font-bold py-3 rounded-lg transition-all flex items-center justify-center gap-2 group-hover:translate-y-[-2px] ${user?.is_premium
                            ? 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-lg shadow-purple-900/40'
                            : 'bg-gray-800 text-gray-400 cursor-not-allowed border border-gray-700'
                            }`}
                    >
                        {loading ? (
                            <span className="animate-pulse">Gerando PDF...</span>
                        ) : (
                            <>
                                <span>{user?.is_premium ? 'Baixar Análise PDF' : 'Desbloquear Acesso Pro'}</span>
                                {user?.is_premium && <span className="text-lg">DOWNLOAD</span>}
                            </>
                        )}
                    </button>
                    {downloadError && (
                        <p className="text-center text-red-400 text-xs">{downloadError}</p>
                    )}
                </div>
            </div>
        </div>
    );
}
