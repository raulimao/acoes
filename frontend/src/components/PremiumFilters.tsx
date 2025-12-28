'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Filter,
    Lock,
    ChevronDown,
    X,
    Zap,
    Building2,
    TrendingUp,
    Percent,
    BarChart3,
    DollarSign,
    Activity,
    Target,
    Sparkles
} from 'lucide-react';

interface PremiumFiltersProps {
    isPremium: boolean;
    sectors: string[];
    onFiltersChange: (filters: FilterValues) => void;
    onUpgradeClick: () => void;
}

export interface FilterValues {
    setor: string | null;
    subsetor: string | null;
    minPl: number | null;
    maxPl: number | null;
    minPvp: number | null;
    maxPvp: number | null;
    minDy: number | null;
    minRoe: number | null;
    minRoic: number | null;
    minGraham: number | null;
    minGreenblatt: number | null;
    minBazin: number | null;
    minQualidade: number | null;
    minLiquidity: number | null;
    companyType: string | null;
    minMargin: number | null;
    minGrowth: number | null;
}

const defaultFilters: FilterValues = {
    setor: null,
    subsetor: null,
    minPl: null,
    maxPl: null,
    minPvp: null,
    maxPvp: null,
    minDy: null,
    minRoe: null,
    minRoic: null,
    minGraham: null,
    minGreenblatt: null,
    minBazin: null,
    minQualidade: null,
    minLiquidity: null,
    companyType: null,
    minMargin: null,
    minGrowth: null,
};

export default function PremiumFilters({ isPremium, sectors, onFiltersChange, onUpgradeClick }: PremiumFiltersProps) {
    const [isExpanded, setIsExpanded] = useState(false);
    const [filters, setFilters] = useState<FilterValues>(defaultFilters);
    const [activeFiltersCount, setActiveFiltersCount] = useState(0);

    useEffect(() => {
        // Count active filters
        const count = Object.values(filters).filter(v => v !== null && v !== '').length;
        setActiveFiltersCount(count);
        onFiltersChange(filters);
    }, [filters]);

    const updateFilter = (key: keyof FilterValues, value: any) => {
        if (!isPremium) {
            onUpgradeClick();
            return;
        }
        setFilters(prev => ({ ...prev, [key]: value || null }));
    };

    const clearFilters = () => {
        setFilters(defaultFilters);
    };

    const FilterLock = ({ children, label }: { children: React.ReactNode; label: string }) => {
        if (isPremium) return <>{children}</>;

        return (
            <div className="relative group">
                <div className="opacity-50 pointer-events-none blur-[1px]">
                    {children}
                </div>
                <div
                    className="absolute inset-0 flex items-center justify-center cursor-pointer"
                    onClick={onUpgradeClick}
                >
                    <div className="bg-slate-800/90 backdrop-blur-sm rounded-lg px-3 py-1 flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Lock className="w-3 h-3 text-yellow-400" />
                        <span className="text-xs text-yellow-400 font-medium">Premium</span>
                    </div>
                </div>
            </div>
        );
    };

    return (
        <motion.div
            className="card mb-6 overflow-hidden"
            initial={false}
        >
            {/* Header */}
            <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
                        <Filter className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <h3 className="font-bold text-white flex items-center gap-2">
                            Filtros Inteligentes
                            {!isPremium && (
                                <span className="px-2 py-0.5 rounded-full bg-yellow-500/20 text-yellow-400 text-xs font-medium flex items-center gap-1">
                                    <Lock className="w-3 h-3" />
                                    Premium
                                </span>
                            )}
                        </h3>
                        <p className="text-white/50 text-sm">
                            {activeFiltersCount > 0
                                ? `${activeFiltersCount} filtro(s) ativo(s)`
                                : '15 filtros disponíveis'}
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    {activeFiltersCount > 0 && (
                        <button
                            onClick={(e) => { e.stopPropagation(); clearFilters(); }}
                            className="text-xs text-white/50 hover:text-white flex items-center gap-1"
                        >
                            <X className="w-3 h-3" />
                            Limpar
                        </button>
                    )}
                    <motion.div
                        animate={{ rotate: isExpanded ? 180 : 0 }}
                        transition={{ duration: 0.2 }}
                    >
                        <ChevronDown className="w-5 h-5 text-white/50" />
                    </motion.div>
                </div>
            </div>

            {/* Filters Content */}
            <AnimatePresence>
                {isExpanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="overflow-hidden"
                    >
                        <div className="pt-6 border-t border-white/10 mt-4">
                            {/* Upgrade Banner for Free Users */}
                            {!isPremium && (
                                <motion.div
                                    className="mb-6 p-4 rounded-xl bg-gradient-to-r from-yellow-500/20 to-orange-500/20 border border-yellow-500/30"
                                    initial={{ y: -10, opacity: 0 }}
                                    animate={{ y: 0, opacity: 1 }}
                                >
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            <Sparkles className="w-6 h-6 text-yellow-400" />
                                            <div>
                                                <p className="font-bold text-white">Desbloqueie 15 Filtros Premium</p>
                                                <p className="text-sm text-white/60">Encontre as ações perfeitas para seu perfil</p>
                                            </div>
                                        </div>
                                        <button
                                            onClick={onUpgradeClick}
                                            className="px-4 py-2 bg-gradient-to-r from-yellow-400 to-orange-500 text-black font-bold rounded-lg text-sm hover:scale-105 transition-transform"
                                        >
                                            Assinar Pro
                                        </button>
                                    </div>
                                </motion.div>
                            )}

                            {/* Filter Grid */}
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                                {/* SETOR */}
                                <div className="space-y-2">
                                    <label className="text-xs text-white/50 flex items-center gap-1">
                                        <Building2 className="w-3 h-3" />
                                        Setor
                                    </label>
                                    <FilterLock label="Setor">
                                        <select
                                            value={filters.setor || ''}
                                            onChange={(e) => updateFilter('setor', e.target.value)}
                                            className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                                        >
                                            <option value="">Todos os setores</option>
                                            {sectors.map(s => (
                                                <option key={s} value={s}>{s}</option>
                                            ))}
                                        </select>
                                    </FilterLock>
                                </div>

                                {/* TIPO EMPRESA */}
                                <div className="space-y-2">
                                    <label className="text-xs text-white/50 flex items-center gap-1">
                                        <Target className="w-3 h-3" />
                                        Tipo de Empresa
                                    </label>
                                    <FilterLock label="Tipo">
                                        <select
                                            value={filters.companyType || ''}
                                            onChange={(e) => updateFilter('companyType', e.target.value)}
                                            className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                                        >
                                            <option value="">Todas</option>
                                            <option value="blue_chips">💎 Blue Chips</option>
                                            <option value="mid_caps">📊 Mid Caps</option>
                                            <option value="small_caps">🚀 Small Caps</option>
                                        </select>
                                    </FilterLock>
                                </div>

                                {/* P/L Range */}
                                <div className="space-y-2">
                                    <label className="text-xs text-white/50 flex items-center gap-1">
                                        <BarChart3 className="w-3 h-3" />
                                        P/L (Preço/Lucro)
                                    </label>
                                    <FilterLock label="P/L">
                                        <div className="flex gap-2">
                                            <input
                                                type="number"
                                                placeholder="Min"
                                                value={filters.minPl || ''}
                                                onChange={(e) => updateFilter('minPl', parseFloat(e.target.value))}
                                                className="w-1/2 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                                            />
                                            <input
                                                type="number"
                                                placeholder="Max"
                                                value={filters.maxPl || ''}
                                                onChange={(e) => updateFilter('maxPl', parseFloat(e.target.value))}
                                                className="w-1/2 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                                            />
                                        </div>
                                    </FilterLock>
                                </div>

                                {/* P/VP Range */}
                                <div className="space-y-2">
                                    <label className="text-xs text-white/50 flex items-center gap-1">
                                        <BarChart3 className="w-3 h-3" />
                                        P/VP (Preço/Valor)
                                    </label>
                                    <FilterLock label="P/VP">
                                        <div className="flex gap-2">
                                            <input
                                                type="number"
                                                placeholder="Min"
                                                step="0.1"
                                                value={filters.minPvp || ''}
                                                onChange={(e) => updateFilter('minPvp', parseFloat(e.target.value))}
                                                className="w-1/2 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                                            />
                                            <input
                                                type="number"
                                                placeholder="Max"
                                                step="0.1"
                                                value={filters.maxPvp || ''}
                                                onChange={(e) => updateFilter('maxPvp', parseFloat(e.target.value))}
                                                className="w-1/2 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                                            />
                                        </div>
                                    </FilterLock>
                                </div>

                                {/* Dividend Yield */}
                                <div className="space-y-2">
                                    <label className="text-xs text-white/50 flex items-center gap-1">
                                        <DollarSign className="w-3 h-3" />
                                        Dividend Yield Mínimo
                                    </label>
                                    <FilterLock label="DY">
                                        <div className="relative">
                                            <input
                                                type="number"
                                                placeholder="Ex: 6"
                                                step="0.5"
                                                value={filters.minDy || ''}
                                                onChange={(e) => updateFilter('minDy', parseFloat(e.target.value))}
                                                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 pr-8 text-sm text-white focus:border-cyan-500 focus:outline-none"
                                            />
                                            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 text-sm">%</span>
                                        </div>
                                    </FilterLock>
                                </div>

                                {/* ROE */}
                                <div className="space-y-2">
                                    <label className="text-xs text-white/50 flex items-center gap-1">
                                        <TrendingUp className="w-3 h-3" />
                                        ROE Mínimo
                                    </label>
                                    <FilterLock label="ROE">
                                        <div className="relative">
                                            <input
                                                type="number"
                                                placeholder="Ex: 15"
                                                value={filters.minRoe || ''}
                                                onChange={(e) => updateFilter('minRoe', parseFloat(e.target.value))}
                                                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 pr-8 text-sm text-white focus:border-cyan-500 focus:outline-none"
                                            />
                                            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 text-sm">%</span>
                                        </div>
                                    </FilterLock>
                                </div>

                                {/* ROIC */}
                                <div className="space-y-2">
                                    <label className="text-xs text-white/50 flex items-center gap-1">
                                        <Activity className="w-3 h-3" />
                                        ROIC Mínimo
                                    </label>
                                    <FilterLock label="ROIC">
                                        <div className="relative">
                                            <input
                                                type="number"
                                                placeholder="Ex: 10"
                                                value={filters.minRoic || ''}
                                                onChange={(e) => updateFilter('minRoic', parseFloat(e.target.value))}
                                                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 pr-8 text-sm text-white focus:border-cyan-500 focus:outline-none"
                                            />
                                            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 text-sm">%</span>
                                        </div>
                                    </FilterLock>
                                </div>

                                {/* Margem Líquida */}
                                <div className="space-y-2">
                                    <label className="text-xs text-white/50 flex items-center gap-1">
                                        <Percent className="w-3 h-3" />
                                        Margem Líquida Mínima
                                    </label>
                                    <FilterLock label="Margem">
                                        <div className="relative">
                                            <input
                                                type="number"
                                                placeholder="Ex: 10"
                                                value={filters.minMargin || ''}
                                                onChange={(e) => updateFilter('minMargin', parseFloat(e.target.value))}
                                                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 pr-8 text-sm text-white focus:border-cyan-500 focus:outline-none"
                                            />
                                            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 text-sm">%</span>
                                        </div>
                                    </FilterLock>
                                </div>
                            </div>

                            {/* Strategy Scores Row */}
                            <div className="mt-6 pt-4 border-t border-white/5">
                                <h4 className="text-sm font-medium text-white/70 mb-3 flex items-center gap-2">
                                    <Zap className="w-4 h-4 text-yellow-400" />
                                    Scores por Estratégia
                                </h4>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    {/* Graham */}
                                    <div className="space-y-2">
                                        <label className="text-xs text-white/50">Score Graham</label>
                                        <FilterLock label="Graham">
                                            <input
                                                type="number"
                                                placeholder="Min"
                                                step="0.5"
                                                max="5"
                                                value={filters.minGraham || ''}
                                                onChange={(e) => updateFilter('minGraham', parseFloat(e.target.value))}
                                                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                                            />
                                        </FilterLock>
                                    </div>

                                    {/* Greenblatt */}
                                    <div className="space-y-2">
                                        <label className="text-xs text-white/50">Score Greenblatt</label>
                                        <FilterLock label="Greenblatt">
                                            <input
                                                type="number"
                                                placeholder="Min"
                                                step="0.5"
                                                max="5"
                                                value={filters.minGreenblatt || ''}
                                                onChange={(e) => updateFilter('minGreenblatt', parseFloat(e.target.value))}
                                                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                                            />
                                        </FilterLock>
                                    </div>

                                    {/* Bazin */}
                                    <div className="space-y-2">
                                        <label className="text-xs text-white/50">Score Bazin</label>
                                        <FilterLock label="Bazin">
                                            <input
                                                type="number"
                                                placeholder="Min"
                                                step="0.5"
                                                max="5"
                                                value={filters.minBazin || ''}
                                                onChange={(e) => updateFilter('minBazin', parseFloat(e.target.value))}
                                                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                                            />
                                        </FilterLock>
                                    </div>

                                    {/* Qualidade */}
                                    <div className="space-y-2">
                                        <label className="text-xs text-white/50">Score Qualidade</label>
                                        <FilterLock label="Qualidade">
                                            <input
                                                type="number"
                                                placeholder="Min"
                                                step="0.5"
                                                max="7"
                                                value={filters.minQualidade || ''}
                                                onChange={(e) => updateFilter('minQualidade', parseFloat(e.target.value))}
                                                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                                            />
                                        </FilterLock>
                                    </div>
                                </div>
                            </div>

                            {/* Liquidity and Growth Row */}
                            <div className="mt-6 pt-4 border-t border-white/5">
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    {/* Liquidez */}
                                    <div className="space-y-2">
                                        <label className="text-xs text-white/50">Liquidez Mínima</label>
                                        <FilterLock label="Liquidez">
                                            <select
                                                value={filters.minLiquidity || ''}
                                                onChange={(e) => updateFilter('minLiquidity', parseFloat(e.target.value))}
                                                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none"
                                            >
                                                <option value="">Qualquer</option>
                                                <option value="1000000">{'> R$ 1M'}</option>
                                                <option value="10000000">{'> R$ 10M'}</option>
                                                <option value="50000000">{'> R$ 50M'}</option>
                                                <option value="100000000">{'> R$ 100M'}</option>
                                            </select>
                                        </FilterLock>
                                    </div>

                                    {/* Crescimento */}
                                    <div className="space-y-2">
                                        <label className="text-xs text-white/50">Crescimento Receita 5a</label>
                                        <FilterLock label="Crescimento">
                                            <div className="relative">
                                                <input
                                                    type="number"
                                                    placeholder="Min"
                                                    value={filters.minGrowth || ''}
                                                    onChange={(e) => updateFilter('minGrowth', parseFloat(e.target.value))}
                                                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 pr-8 text-sm text-white focus:border-cyan-500 focus:outline-none"
                                                />
                                                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 text-sm">%</span>
                                            </div>
                                        </FilterLock>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
}
