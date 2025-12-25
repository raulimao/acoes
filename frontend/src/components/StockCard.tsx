import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Lock, Zap, AlertTriangle } from 'lucide-react';
import PremiumLock from './PremiumLock';

interface Stock {
    papel: string;
    setor?: string;
    cotacao?: number;
    p_l?: number;
    p_vp?: number;
    dividend_yield?: number;
    super_score?: number;
    score_graham?: number;
}

interface StockCardProps {
    stock: Stock;
    index: number;
    isPremium: boolean;
    onClick: (stock: Stock) => void;
    isSelected?: boolean;
    onToggleSelect?: (stock: Stock) => void;
}

export default function StockCard({ stock, index, isPremium, onClick, isSelected, onToggleSelect }: StockCardProps) {
    // Ruthless Freemium: Only Top 1 is free. Index 0 is free.
    const isLocked = !isPremium && index > 0;

    const getScoreColor = (score: number) => {
        if (score >= 12) return 'score-high';
        if (score >= 8) return 'score-medium';
        return 'score-low';
    };

    // Calculate Graham Price (Preço Teto)
    // Formula: Price * Sqrt(22.5 / (P/L * P/VP))
    // Derived from: Graham = Sqrt(22.5 * LPA * VPA)
    let grahamPrice = 0;
    let upside = 0;
    let isGrahamValid = false;

    if (stock.cotacao && stock.p_l && stock.p_vp && stock.p_l > 0 && stock.p_vp > 0) {
        grahamPrice = stock.cotacao * Math.sqrt(22.5 / (stock.p_l * stock.p_vp));
        upside = ((grahamPrice - stock.cotacao) / stock.cotacao) * 100;
        isGrahamValid = true;
    }

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.05 }}
            className={`card relative group overflow-visible ${isLocked ? 'cursor-not-allowed' : 'cursor-pointer hover:border-cyan-400/50 hover:shadow-lg hover:shadow-cyan-400/10'} ${isSelected ? 'border-yellow-400 ring-1 ring-yellow-400' : ''}`}
            onClick={() => !isLocked && onClick(stock)}
        >
            {/* Selection Checkbox for Battle */}
            {!isLocked && onToggleSelect && (
                <div
                    className="absolute -top-3 -right-3 z-30 opacity-0 group-hover:opacity-100 transition-opacity"
                    style={{ opacity: isSelected ? 1 : undefined }}
                >
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            onToggleSelect(stock);
                        }}
                        className={`w-8 h-8 rounded-full flex items-center justify-center border transition-all shadow-lg ${isSelected ? 'bg-yellow-400 border-yellow-400 text-slate-900 scale-110' : 'bg-slate-800 border-white/20 text-white/20 hover:border-yellow-400 hover:text-yellow-400'}`}
                        title="Comparar (Batalha)"
                    >
                        <Zap className="w-4 h-4" />
                    </button>
                </div>
            )}

            {isLocked && (
                <div className="absolute inset-0 z-20">
                    {index === 1 ? (
                        <PremiumLock title="Desbloqueie o Ranking" description="Acesse 100+ oportunidades de alto valor." />
                    ) : (
                        <div className="absolute inset-0 backdrop-blur-sm bg-slate-950/60 flex flex-col items-center justify-center text-center p-6">
                            <div className="p-4 bg-white/5 rounded-full mb-3 animate-pulse">
                                <Lock className="w-8 h-8 text-white/50" />
                            </div>
                            <p className="text-white/60 font-semibold mb-2">Acesso Restrito</p>
                            <button className="px-4 py-2 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-500/50 text-cyan-400 rounded-lg text-xs font-bold hover:bg-cyan-500/30 transition-all">
                                Seja PRO
                            </button>
                        </div>
                    )}
                </div>
            )}

            <div className={isLocked ? 'blur-sm select-none opacity-50' : ''}>
                <div className="flex justify-between items-start mb-4">
                    <div>
                        <div className="flex items-center gap-2 mb-1">
                            <h3 className="text-xl font-bold text-white">{stock.papel}</h3>
                            <span className="text-xs text-white/40 px-2 py-0.5 rounded-full bg-white/5 border border-white/10">
                                {stock.setor || 'Diversos'}
                            </span>
                        </div>
                        <p className="text-2xl font-bold gradient-text">
                            R$ {stock.cotacao?.toFixed(2)}
                        </p>
                    </div>
                    <div className={`score-badge ${getScoreColor(stock.super_score || 0)}`}>
                        <Zap className="w-4 h-4 mr-1" />
                        {stock.super_score?.toFixed(1)}
                    </div>
                </div>

                {/* Preço Teto / Graham */}
                <div className="mb-4 bg-white/5 rounded-lg p-3 border border-white/5">
                    <div className="flex justify-between items-center mb-1">
                        <span className="text-xs text-white/40 flex items-center gap-1">
                            <TrendingUp className="w-3 h-3" /> Preço Teto (Graham)
                        </span>
                        {!isGrahamValid ? (
                            <span className="text-xs text-white/20">N/A</span>
                        ) : upside > 0 ? (
                            <span className="text-xs text-green-400 font-bold">+{upside.toFixed(0)}% Upside</span>
                        ) : (
                            <span className="text-xs text-red-400 font-bold">{upside.toFixed(0)}% Downside</span>
                        )}
                    </div>
                    {isGrahamValid ? (
                        <div className="flex items-end gap-2">
                            <span className={`text-lg font-bold ${upside > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                R$ {grahamPrice.toFixed(2)}
                            </span>
                            <span className="text-xs text-white/30 mb-1">
                                {upside > 20 ? '🚀 Oportunidade' : upside < -20 ? '⚠️ Cuidado' : 'Neutro'}
                            </span>
                        </div>
                    ) : (
                        <div className="text-xs text-white/30 italic">
                            Dados insuficientes
                        </div>
                    )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <p className="text-white/40 text-xs mb-1">P/L</p>
                        <p className="font-semibold text-white/90">{stock.p_l?.toFixed(2)}</p>
                    </div>
                    <div>
                        <p className="text-white/40 text-xs mb-1">Div. Yield</p>
                        <p className={`font-semibold ${stock.dividend_yield && stock.dividend_yield > 6 ? 'text-green-400' : 'text-white/90'}`}>
                            {stock.dividend_yield ? stock.dividend_yield.toFixed(2) : '0.00'}%
                        </p>
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
