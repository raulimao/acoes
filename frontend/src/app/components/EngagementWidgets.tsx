'use client';
import { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
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
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState(true);

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

    const downloadReport = () => {
        if (user?.is_premium) {
            window.open(`${API_URL}/reports/weekly`, '_blank');
        } else {
            alert("🔒 Recurso Premium: Assine o Pro para baixar relatórios semanais em PDF.");
            // In a real app, open a modal or redirect to pricing
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

            {/* Weekly Report Widget */}
            <div className={`relative rounded-xl p-6 border flex flex-col justify-between overflow-hidden ${user?.is_premium
                ? 'bg-gradient-to-br from-purple-900 to-indigo-900 border-purple-700'
                : 'bg-gray-900 border-gray-700 opacity-80'
                }`}>
                <div>
                    <h3 className="text-xl font-bold text-white mb-2 flex items-center justify-between">
                        📄 Relatório Semanal
                        {!user?.is_premium && <Lock className="w-5 h-5 text-gray-500" />}
                    </h3>
                    <p className={`${user?.is_premium ? 'text-purple-200' : 'text-gray-400'} text-sm mb-4`}>
                        Baixe o resumo completo do mercado, Top 10 e carteiras sugeridas em PDF.
                    </p>
                </div>

                <button
                    onClick={downloadReport}
                    className={`w-full font-bold py-3 rounded-lg transition-colors flex items-center justify-center gap-2 ${user?.is_premium
                        ? 'bg-white text-purple-900 hover:bg-purple-100'
                        : 'bg-gray-700 text-gray-400 cursor-not-allowed hover:bg-gray-600'
                        }`}
                >
                    <span>{user?.is_premium ? '📥 Baixar PDF' : '🔒 Bloqueado (Pro)'}</span>
                </button>
            </div>
        </div>
    );
}
