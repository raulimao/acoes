import React from 'react';
import { motion } from 'framer-motion';
import { Zap } from 'lucide-react';

interface Stock {
    papel: string;
    setor?: string;
    cotacao?: number;
    p_l?: number;
    p_vp?: number;
    dividend_yield?: number;
    super_score?: number;
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
    const getScoreColor = (score: number) => {
        if (score >= 12) return 'text-green-400 bg-green-500/20';
        if (score >= 8) return 'text-yellow-400 bg-yellow-500/20';
        return 'text-red-400 bg-red-500/20';
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.03 }}
            className={`rounded-xl bg-slate-800/60 border border-white/10 p-4 cursor-pointer hover:border-cyan-400/50 hover:bg-slate-800/80 transition-all ${isSelected ? 'border-yellow-400 ring-1 ring-yellow-400' : ''}`}
            onClick={() => onClick(stock)}
        >
            {/* Header: Name + Score */}
            <div className="flex justify-between items-start mb-3">
                <div>
                    <h3 className="text-lg font-bold text-white">{stock.papel}</h3>
                    <p className="text-xs text-white/40">{stock.setor?.slice(0, 20) || 'N/A'}</p>
                </div>
                <div className={`px-2 py-1 rounded-lg text-sm font-bold flex items-center gap-1 ${getScoreColor(stock.super_score || 0)}`}>
                    <Zap className="w-3 h-3" />
                    {stock.super_score !== undefined ? stock.super_score.toFixed(1) : '0.0'}
                </div>
            </div>

            {/* Price */}
            <p className="text-xl font-bold text-white mb-3">
                R$ {stock.cotacao !== undefined ? stock.cotacao.toFixed(2) : '--'}
            </p>

            {/* Key Metrics - Only 3 */}
            <div className="grid grid-cols-3 gap-2 text-center">
                <div className="bg-white/5 rounded-lg py-2">
                    <p className="text-xs text-white/40">P/L</p>
                    <p className="text-sm font-semibold text-white">{stock.p_l?.toFixed(1) || 'N/A'}</p>
                </div>
                <div className="bg-white/5 rounded-lg py-2">
                    <p className="text-xs text-white/40">P/VP</p>
                    <p className="text-sm font-semibold text-white">{stock.p_vp?.toFixed(1) || 'N/A'}</p>
                </div>
                <div className="bg-white/5 rounded-lg py-2">
                    <p className="text-xs text-white/40">DY</p>
                    <p className={`text-sm font-semibold ${stock.dividend_yield && stock.dividend_yield > 6 ? 'text-green-400' : 'text-white'}`}>
                        {stock.dividend_yield?.toFixed(1) || '0'}%
                    </p>
                </div>
            </div>

            {/* Battle Selection Button - Always Visible */}
            {onToggleSelect && (
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onToggleSelect(stock);
                    }}
                    className={`mt-3 w-full py-2.5 rounded-lg text-sm font-bold transition-all flex items-center justify-center gap-2 ${isSelected
                        ? 'bg-yellow-400 text-black border-2 border-yellow-300'
                        : 'bg-purple-600/30 text-purple-300 border border-purple-500/50 hover:bg-purple-600/50 hover:text-white'
                        }`}
                >
                    <Zap className="w-4 h-4" />
                    {isSelected ? '✓ Selecionado para Batalha' : '⚔️ Comparar Ação'}
                </button>
            )}
        </motion.div>
    );
}
