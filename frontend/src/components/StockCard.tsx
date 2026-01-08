import React from 'react';
import { motion } from 'framer-motion';
import { Zap, AlertTriangle, Droplets, TrendingDown } from 'lucide-react';

interface Stock {
    papel: string;
    setor?: string;
    cotacao?: number;
    p_l?: number;
    p_vp?: number;
    dividend_yield?: number;
    super_score?: number;
    fusion_score?: number;
    roe?: number;
    red_flags?: string[];
}

interface StockCardProps {
    stock: Stock;
    index: number;
    isPremium: boolean;
    onClick: (stock: Stock) => void;
    isSelected?: boolean;
    onToggleSelect?: (stock: Stock) => void;
}

export default function StockCard({ stock, index, onClick, isSelected, onToggleSelect }: StockCardProps) {
    // Helper to get flag details
    const getFlagDetails = (flag: string) => {
        switch (flag) {
            case 'LOW_LIQ': return { icon: Droplets, color: 'text-orange-400' };
            case 'DIV_TRAP': return { icon: AlertTriangle, color: 'text-red-500' };
            case 'HIGH_DEBT': return { icon: TrendingDown, color: 'text-red-400' };
            case 'LOW_MARGIN': return { icon: AlertTriangle, color: 'text-yellow-400' };
            case 'STAGNANT': return { icon: TrendingDown, color: 'text-purple-400' };
            case 'CYCLICAL': return { icon: AlertTriangle, color: 'text-amber-400' };
            case 'REGULATED': return { icon: AlertTriangle, color: 'text-blue-400' };
            default: return null;
        }
    };

    const displayScore = stock.fusion_score ?? (stock.super_score && stock.super_score > 30 ? stock.super_score : (stock.super_score ?? 0));
    const isPercentScale = (stock.fusion_score !== undefined) || (stock.super_score && stock.super_score > 30);

    const getScoreColor = (score: number) => {
        if (isPercentScale) {
            if (score >= 80) return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
            if (score >= 60) return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
            return 'text-red-400 bg-red-500/10 border-red-500/20';
        }
        if (score >= 12) return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
        if (score >= 8) return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
        return 'text-red-400 bg-red-500/10 border-red-500/20';
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.03 }}
            className={`universal-asset-card group ${isSelected ? 'ring-2 ring-yellow-400/50 border-yellow-400/50' : ''}`}
            onClick={() => onClick(stock)}
        >
            {/* Header: Ticker + Score & Price */}
            <div className="flex justify-between items-start mb-1">
                <div className="flex items-center gap-2">
                    <h3 className="asset-ticker">{stock.papel}</h3>
                    <div className={`px-1.5 py-0.5 rounded border text-[10px] font-bold ${getScoreColor(displayScore)}`}>
                        {displayScore.toFixed(1)}
                    </div>
                </div>
                <div className="asset-price">
                    R$ {stock.cotacao !== undefined ? stock.cotacao.toFixed(2) : '--'}
                </div>
            </div>

            {/* Sector */}
            <p className="text-[10px] text-white/30 font-bold uppercase tracking-wider mb-4">
                {stock.setor ? String(stock.setor).slice(0, 24) : 'N/A'}
            </p>

            {/* Standardized 3-column Metric Grid */}
            <div className="grid grid-cols-3 gap-2 py-4 border-y border-white/5 my-2">
                <div className="text-center">
                    <p className="card-metric-label">P/L</p>
                    <p className="card-metric-value">{stock.p_l?.toFixed(1) || '0.0'}</p>
                </div>
                <div className="text-center border-x border-white/5">
                    <p className="card-metric-label">DY</p>
                    <p className={`card-metric-value ${stock.dividend_yield && stock.dividend_yield > 0.06 ? 'text-emerald-400' : ''}`}>
                        {stock.dividend_yield ? (stock.dividend_yield * 100).toFixed(1) : '0'}%
                    </p>
                </div>
                <div className="text-center">
                    <p className="card-metric-label">ROE</p>
                    <p className="card-metric-value">{stock.roe ? (stock.roe * 100).toFixed(1) : 'N/A'}</p>
                </div>
            </div>

            {/* Footer: Flags & Comparison CTA */}
            <div className="flex items-center justify-between mt-3">
                <div className="flex items-center gap-1.5">
                    {stock.red_flags?.slice(0, 3).map((flag) => {
                        const details = getFlagDetails(flag);
                        if (!details) return null;
                        const Icon = details.icon;
                        return (
                            <div key={flag} className={`p-1.5 rounded-lg bg-white/5 ${details.color}`} title={flag}>
                                <Icon className="w-3.5 h-3.5" />
                            </div>
                        );
                    })}
                </div>

                {onToggleSelect && (
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            onToggleSelect(stock);
                        }}
                        className={`p-2 rounded-lg transition-all ${isSelected
                            ? 'bg-yellow-400 text-black shadow-lg shadow-yellow-400/20'
                            : 'bg-white/5 text-white/20 hover:bg-white/10 hover:text-white'
                            }`}
                        title={isSelected ? 'Remover da Batalha' : 'Comparar Ação'}
                    >
                        <Zap className={`w-4 h-4 ${isSelected ? 'fill-current' : ''}`} />
                    </button>
                )}
            </div>
        </motion.div>
    );
}
