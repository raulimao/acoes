'use client';
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

interface Stock {
    ticker: string;
    sector: string;
    price: number;
    super_score: number;
    p_l: number;
    dividend_yield: number;
    roe: number;
    liquidity: number;
    reason: string;
}

interface PortfolioData {
    profile: string;
    criteria: {
        description: string;
        objective: string;
        filters: string;
    };
    stocks: Stock[];
    disclaimer: string;
}

const PROFILES = [
    {
        id: 'conservador',
        name: 'Conservador',
        icon: '🛡️',
        description: 'Foco em dividendos e segurança'
    },
    {
        id: 'moderado',
        name: 'Moderado',
        icon: '⚖️',
        description: 'Equilíbrio entre renda e crescimento'
    },
    {
        id: 'agressivo',
        name: 'Agressivo',
        icon: '🚀',
        description: 'Foco em crescimento e valorização'
    }
];

export default function SuggestedPortfolio() {
    const [selectedProfile, setSelectedProfile] = useState<string>('moderado');
    const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
    const [loading, setLoading] = useState(false);
    const [isOpen, setIsOpen] = useState(false);

    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let abortController: AbortController | null = null;

        const fetchPortfolio = async () => {
            if (abortController) abortController.abort();
            abortController = new AbortController();

            setLoading(true);
            setError(null);

            try {
                const response = await axios.post(
                    `${API_URL}/portfolio/suggested`,
                    { profile: selectedProfile },
                    { signal: abortController.signal }
                );
                setPortfolio(response.data);
            } catch (error: unknown) {
                if (axios.isCancel(error)) return;
                console.error('Error fetching portfolio:', error);
                setError('Erro ao gerar sugestão. Tente novamente.');
            } finally {
                if (abortController && !abortController.signal.aborted) {
                    setLoading(false);
                }
            }
        };

        if (isOpen) {
            fetchPortfolio();
        }

        return () => {
            if (abortController) abortController.abort();
        };
    }, [selectedProfile, isOpen]);

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
    };

    const formatLiquidity = (value: number) => {
        if (value >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(1)}B`;
        if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
        if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
        return value.toString();
    };

    return (
        <>
            {/* Floating Button */}
            <motion.button
                onClick={() => setIsOpen(true)}
                className="fixed bottom-24 right-6 z-40"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                style={{
                    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                    borderRadius: '1rem',
                    padding: '0.75rem 1.25rem',
                    color: 'white',
                    fontWeight: 600,
                    boxShadow: '0 4px 20px rgba(16, 185, 129, 0.4)',
                    border: 'none',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem'
                }}
            >
                <span style={{ fontSize: '1.25rem' }}>💼</span>
                <span>Minha Carteira</span>
            </motion.button>

            {/* Modal */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setIsOpen(false)}
                        style={{
                            position: 'fixed',
                            inset: 0,
                            background: 'rgba(0, 0, 0, 0.7)',
                            backdropFilter: 'blur(4px)',
                            zIndex: 50,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            padding: '1rem'
                        }}
                    >
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            onClick={(e) => e.stopPropagation()}
                            style={{
                                background: 'linear-gradient(180deg, #1f2937 0%, #111827 100%)',
                                borderRadius: '1.5rem',
                                maxWidth: '900px',
                                width: '100%',
                                maxHeight: '90vh',
                                overflow: 'auto',
                                border: '1px solid rgba(16, 185, 129, 0.2)',
                                boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
                            }}
                        >
                            {/* Header */}
                            <div style={{
                                padding: '1.5rem',
                                borderBottom: '1px solid rgba(255,255,255,0.1)',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center'
                            }}>
                                <div>
                                    <h2 style={{
                                        color: 'white',
                                        fontSize: '1.5rem',
                                        fontWeight: 700,
                                        margin: 0
                                    }}>
                                        💼 Carteira Sugerida
                                    </h2>
                                    <p style={{ color: 'rgba(255,255,255,0.6)', margin: '0.25rem 0 0', fontSize: '0.9rem' }}>
                                        Selecionamos 5 ações baseadas no seu perfil
                                    </p>
                                </div>
                                <button
                                    onClick={() => setIsOpen(false)}
                                    style={{
                                        background: 'rgba(255,255,255,0.1)',
                                        border: 'none',
                                        borderRadius: '0.5rem',
                                        color: 'white',
                                        padding: '0.5rem 1rem',
                                        cursor: 'pointer'
                                    }}
                                >
                                    ✕
                                </button>
                            </div>

                            {/* Profile Selector */}
                            <div style={{ padding: '1rem 1.5rem' }}>
                                <p style={{ color: 'rgba(255,255,255,0.7)', marginBottom: '0.75rem', fontSize: '0.9rem' }}>
                                    Selecione seu perfil de investidor:
                                </p>
                                <div style={{ display: 'flex', gap: '1rem' }}>
                                    {PROFILES.map(profile => (
                                        <motion.button
                                            key={profile.id}
                                            onClick={() => setSelectedProfile(profile.id)}
                                            whileHover={{ scale: 1.02 }}
                                            whileTap={{ scale: 0.98 }}
                                            style={{
                                                flex: 1,
                                                padding: '1rem',
                                                borderRadius: '1rem',
                                                border: selectedProfile === profile.id
                                                    ? '2px solid #10b981'
                                                    : '1px solid rgba(255,255,255,0.1)',
                                                background: selectedProfile === profile.id
                                                    ? 'rgba(16, 185, 129, 0.15)'
                                                    : 'rgba(255,255,255,0.05)',
                                                cursor: 'pointer',
                                                textAlign: 'center'
                                            }}
                                        >
                                            <span style={{ fontSize: '2rem', display: 'block' }}>{profile.icon}</span>
                                            <span style={{
                                                color: 'white',
                                                fontWeight: 600,
                                                display: 'block',
                                                marginTop: '0.5rem'
                                            }}>
                                                {profile.name}
                                            </span>
                                            <span style={{
                                                color: 'rgba(255,255,255,0.5)',
                                                fontSize: '0.75rem',
                                                display: 'block',
                                                marginTop: '0.25rem'
                                            }}>
                                                {profile.description}
                                            </span>
                                        </motion.button>
                                    ))}
                                </div>
                            </div>

                            {/* Portfolio Content */}
                            <div style={{ padding: '0 1.5rem 1.5rem' }}>
                                {loading ? (
                                    <div style={{ textAlign: 'center', padding: '3rem', color: 'white' }}>
                                        <div className="animate-spin" style={{
                                            width: '40px',
                                            height: '40px',
                                            border: '3px solid rgba(16, 185, 129, 0.3)',
                                            borderTopColor: '#10b981',
                                            borderRadius: '50%',
                                            margin: '0 auto 1rem'
                                        }}></div>
                                        Analisando melhores ações...
                                    </div>
                                ) : portfolio ? (
                                    <>
                                        {/* Criteria Info */}
                                        <div style={{
                                            background: 'rgba(16, 185, 129, 0.1)',
                                            borderRadius: '0.75rem',
                                            padding: '1rem',
                                            marginBottom: '1rem'
                                        }}>
                                            <p style={{ color: '#10b981', fontWeight: 600, margin: 0 }}>
                                                {portfolio.criteria.description}
                                            </p>
                                            <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.85rem', margin: '0.25rem 0 0' }}>
                                                🎯 {portfolio.criteria.objective}
                                            </p>
                                        </div>

                                        {/* Stocks Table */}
                                        <div style={{ overflowX: 'auto' }}>
                                            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                                <thead>
                                                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                                                        <th style={{ textAlign: 'left', padding: '0.75rem', color: 'rgba(255,255,255,0.7)', fontSize: '0.8rem' }}>Ação</th>
                                                        <th style={{ textAlign: 'left', padding: '0.75rem', color: 'rgba(255,255,255,0.7)', fontSize: '0.8rem' }}>Setor</th>
                                                        <th style={{ textAlign: 'right', padding: '0.75rem', color: 'rgba(255,255,255,0.7)', fontSize: '0.8rem' }}>Cotação</th>
                                                        <th style={{ textAlign: 'right', padding: '0.75rem', color: 'rgba(255,255,255,0.7)', fontSize: '0.8rem' }}>Score</th>
                                                        <th style={{ textAlign: 'right', padding: '0.75rem', color: 'rgba(255,255,255,0.7)', fontSize: '0.8rem' }}>DY</th>
                                                        <th style={{ textAlign: 'right', padding: '0.75rem', color: 'rgba(255,255,255,0.7)', fontSize: '0.8rem' }}>Liquidez</th>
                                                        <th style={{ textAlign: 'left', padding: '0.75rem', color: 'rgba(255,255,255,0.7)', fontSize: '0.8rem' }}>Por quê?</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {portfolio.stocks.map((stock, i) => (
                                                        <motion.tr
                                                            key={stock.ticker}
                                                            initial={{ opacity: 0, y: 10 }}
                                                            animate={{ opacity: 1, y: 0 }}
                                                            transition={{ delay: i * 0.1 }}
                                                            style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}
                                                        >
                                                            <td style={{ padding: '1rem 0.75rem' }}>
                                                                <span style={{ color: '#10b981', fontWeight: 700 }}>{stock.ticker}</span>
                                                            </td>
                                                            <td style={{ padding: '1rem 0.75rem', color: 'rgba(255,255,255,0.8)' }}>
                                                                {stock.sector}
                                                            </td>
                                                            <td style={{ padding: '1rem 0.75rem', color: 'white', textAlign: 'right' }}>
                                                                {formatCurrency(stock.price)}
                                                            </td>
                                                            <td style={{ padding: '1rem 0.75rem', textAlign: 'right' }}>
                                                                <span style={{
                                                                    background: 'rgba(139, 92, 246, 0.2)',
                                                                    color: '#a78bfa',
                                                                    padding: '0.25rem 0.5rem',
                                                                    borderRadius: '0.25rem',
                                                                    fontWeight: 600
                                                                }}>
                                                                    {stock.super_score}
                                                                </span>
                                                            </td>
                                                            <td style={{ padding: '1rem 0.75rem', color: '#10b981', textAlign: 'right', fontWeight: 600 }}>
                                                                {stock.dividend_yield}%
                                                            </td>
                                                            <td style={{ padding: '1rem 0.75rem', color: 'rgba(255,255,255,0.6)', textAlign: 'right' }}>
                                                                R$ {formatLiquidity(stock.liquidity)}
                                                            </td>
                                                            <td style={{ padding: '1rem 0.75rem', color: 'rgba(255,255,255,0.6)', fontSize: '0.85rem' }}>
                                                                {stock.reason}
                                                            </td>
                                                        </motion.tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>

                                        {/* Disclaimer */}
                                        <p style={{
                                            color: 'rgba(255,255,255,0.4)',
                                            fontSize: '0.75rem',
                                            marginTop: '1rem',
                                            textAlign: 'center'
                                        }}>
                                            ⚠️ {portfolio.disclaimer}
                                        </p>
                                    </>
                                ) : error ? (
                                    <div style={{ textAlign: 'center', padding: '3rem', color: '#ff6b6b' }}>
                                        <p style={{ fontSize: '3rem', marginBottom: '1rem' }}>⚠️</p>
                                        <p>{error}</p>
                                    </div>
                                ) : null}
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
}
