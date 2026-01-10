'use client';

import { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import {
  Search,
  RefreshCw,
  Sparkles,
  Trophy,
  Zap,
  X,
  LogOut,
  User,
  BarChart3,
  PieChart,
  Target,
  Skull,
  Lock,
  FileText,
  Shield,
  Activity,
  Calculator,
  Briefcase,
  TrendingDown,
  TrendingUp
} from 'lucide-react';
import dynamic from 'next/dynamic';
import StatCard from './components/StatCard';

const AIChat = dynamic(() => import('./components/AIChat'), { ssr: false });
const SuggestedPortfolio = dynamic(() => import('./components/SuggestedPortfolio'), { ssr: false });
const StockComparisonModal = dynamic(() => import('../components/StockComparisonModal'), { ssr: false });
const ToxicStocks = dynamic(() => import('../components/ToxicStocks'), { ssr: false });
const MonitorTab = dynamic(() => import('./components/MonitorTab'), { ssr: false });
const PremiumStockModal = dynamic(() => import('./components/PremiumStockModal'), { ssr: false });
const FusionTab = dynamic(() => import('./components/FusionTab'), { ssr: false });
// Keeping StockCard as static import for LCP optimization (above fold/critical)
import StockCard from '../components/StockCard';
const PremiumFilters = dynamic(() => import('../components/PremiumFilters'), {
  loading: () => <div className="w-full h-32 bg-slate-900/50 border border-slate-800 rounded-xl mb-8 animate-pulse" />,
  ssr: false
});
import type { FilterValues } from '../components/PremiumFilters';
import { useAuth } from './contexts/AuthContext';
import { useDataCache } from './contexts/DataCacheContext';
import { useRouter } from 'next/navigation';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

declare global {
  interface Window {
    abortController?: AbortController;
  }
}

interface Stock {
  papel: string;
  setor?: string;
  subsetor?: string;
  cotacao?: number;
  p_l?: number;
  p_vp?: number;
  dividend_yield?: number;
  roe?: number;
  roic?: number;
  liquidez_corrente?: number;
  score_graham?: number;
  score_greenblatt?: number;
  score_bazin?: number;
  score_qualidade?: number;
  super_score?: number;
  margem_liquida?: number;
  div_bruta_patrimonio?: number;
  crescimento_receita_5a?: number;
  liquidez_2meses?: number;
}

interface Stats {
  total_stocks: number;
  avg_super_score: number;
  top_stock: string;
  top_score: number;
  sectors_count: number;
  opportunities_count: number;
  toxic_count: number;
  market_sentiment: string;
  avg_dividend_yield: number;
  avg_roe: number;
  avg_pl: number;
  best_sector: string;
  avg_growth: number;
}

export default function Dashboard() {
  const router = useRouter();
  const { user, isAuthenticated, loading: authLoading, logout } = useAuth();
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [searchTerm, setSearchTerm] = useState('');
  const [minScore] = useState(5);
  // Legacy Filters (keeping for compatibility)
  const [onlyBlueChips] = useState(false);
  const [onlySmallCaps] = useState(false);

  // New Premium Features
  const [sectors, setSectors] = useState<string[]>([]);
  const [premiumFilters, setPremiumFilters] = useState<FilterValues | null>(null);
  const [displayedStocks, setDisplayedStocks] = useState<Stock[]>([]);
  const [totalStocksCount, setTotalStocksCount] = useState(0);

  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);
  const [notification, setNotification] = useState<{ type: 'success' | 'error', message: string } | null>(null);

  const { getCachedData, setCachedData } = useDataCache();

  // Battle Logic
  const [battleStocks, setBattleStocks] = useState<Stock[]>([]);
  const [showBattleModal, setShowBattleModal] = useState(false);

  const toggleBattleSelection = (stock: Stock) => {
    setBattleStocks(prev => {
      const exists = prev.find(s => s.papel === stock.papel);
      if (exists) {
        return prev.filter(s => s.papel !== stock.papel);
      }
      if (prev.length >= 2) {
        return [prev[1], stock]; // Keep max 2, FIFO
      }
      return [...prev, stock];
    });
  };

  // Fetch sectors on mount
  useEffect(() => {
    const fetchSectors = async () => {
      try {
        const res = await axios.get(`${API_URL}/sectors`);
        setSectors(res.data);
      } catch (error) {
        console.warn('Failed to fetch sectors (using defaults)');
      }
    };
    fetchSectors();
  }, []);

  // Removed redundant useEffect. fetchData dependency handles updates.


  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  // Calculate displayed stocks based on premium status
  useEffect(() => {
    const isPremium = user?.is_premium || false;

    if (isPremium) {
      // Premium users see all stocks
      setDisplayedStocks(stocks);
    } else {
      // Free users see 3 fixed stocks from ranking 16+ (NOT the top 15)
      // Selection is FIXED for the entire week, changes every Sunday

      // Get current week number (resets on Sunday)
      const now = new Date();
      const startOfYear = new Date(now.getFullYear(), 0, 1);
      const dayOfYear = Math.floor((now.getTime() - startOfYear.getTime()) / (24 * 60 * 60 * 1000));
      const weekNumber = Math.floor((dayOfYear + startOfYear.getDay()) / 7);

      // Create a seed from year + week number
      const seed = now.getFullYear() * 100 + weekNumber;

      // Seeded random function (deterministic based on seed)
      const seededRandom = (index: number) => {
        const x = Math.sin(seed + index) * 10000;
        return x - Math.floor(x);
      };

      // Get stocks ranked 16-50
      const belowTop15 = stocks.slice(15, 50);

      if (belowTop15.length >= 3) {
        // Sort using seeded random (same order every time this week)
        const shuffled = [...belowTop15]
          .map((stock, i) => ({ stock, sort: seededRandom(i) }))
          .sort((a, b) => a.sort - b.sort)
          .map(item => item.stock);

        setDisplayedStocks(shuffled.slice(0, 3));
      } else if (belowTop15.length > 0) {
        setDisplayedStocks(belowTop15);
      } else {
        // Fallback if not enough stocks
        setDisplayedStocks(stocks.slice(0, 3));
      }
    }
    setTotalStocksCount(stocks.length);
  }, [stocks, user?.is_premium]);

  // Debug: Log removed
  // useEffect(() => {
  //   console.log('selectedStock state changed:', selectedStock?.papel || 'null');
  // }, [selectedStock]);

  const fetchData = useCallback(async () => {
    // Cancel previous request if exists
    if (window.abortController) {
      window.abortController.abort();
    }
    const controller = new AbortController();
    window.abortController = controller;

    setLoading(true);
    try {
      // For Anti-Ranking, we want distinct logic
      const isAntiRanking = activeTab === 'anti-ranking';
      const isPremium = user?.is_premium || false;

      let endpoint = `${API_URL}/stocks?limit=100`;

      if (isAntiRanking) {
        // Fetch worst stocks
        endpoint += `&max_score=15&sort_by=super_score&order=asc`;
      } else {
        // normal fetching with min score
        endpoint += `&min_score=${minScore}`;
      }

      // Check Cache
      const cacheKey = `dashboard_${activeTab}_${isPremium}_${JSON.stringify(premiumFilters)}`;
      const cached = getCachedData(cacheKey);
      if (cached) {
        setStocks(cached.stocks);
        setStats(cached.stats);
        setLoading(false);
        return;
      }

      // Apply premium filters if set
      if (premiumFilters && isPremium) {
        if (premiumFilters.setor) endpoint += `&setor=${encodeURIComponent(premiumFilters.setor)}`;
        if (premiumFilters.companyType) endpoint += `&company_type=${premiumFilters.companyType}`;
        if (premiumFilters.minPl) endpoint += `&min_pl=${premiumFilters.minPl}`;
        if (premiumFilters.maxPl) endpoint += `&max_pl=${premiumFilters.maxPl}`;
        if (premiumFilters.minPvp) endpoint += `&min_pvp=${premiumFilters.minPvp}`;
        if (premiumFilters.maxPvp) endpoint += `&max_pvp=${premiumFilters.maxPvp}`;
        if (premiumFilters.minDy) endpoint += `&min_dy=${premiumFilters.minDy}`;
        if (premiumFilters.minRoe) endpoint += `&min_roe=${premiumFilters.minRoe}`;
        if (premiumFilters.minRoic) endpoint += `&min_roic=${premiumFilters.minRoic}`;
        if (premiumFilters.minGraham) endpoint += `&min_graham=${premiumFilters.minGraham}`;
        if (premiumFilters.minGreenblatt) endpoint += `&min_greenblatt=${premiumFilters.minGreenblatt}`;
        if (premiumFilters.minBazin) endpoint += `&min_bazin=${premiumFilters.minBazin}`;
        if (premiumFilters.minQualidade) endpoint += `&min_qualidade=${premiumFilters.minQualidade}`;
        if (premiumFilters.minLiquidity) endpoint += `&min_liquidity=${premiumFilters.minLiquidity}`;
        if (premiumFilters.minMargin) endpoint += `&min_margin=${premiumFilters.minMargin}`;
        if (premiumFilters.minGrowth) endpoint += `&min_growth=${premiumFilters.minGrowth}`;
      }

      const [stocksRes, statsRes] = await Promise.all([
        axios.get(endpoint, { signal: controller.signal }),
        axios.get(`${API_URL}/stats`, { signal: controller.signal })
      ]);

      const combinedData = { stocks: stocksRes.data, stats: statsRes.data };
      setCachedData(cacheKey, combinedData);
      setStocks(stocksRes.data);
      setStats(statsRes.data);
    } catch (error: unknown) {
      if (axios.isCancel(error)) {
        console.log('Request canceled', (error as Error).message);
        return;
      }
      console.warn('Error fetching stock data (network or server issue)');
      showNotification('error', 'Erro ao carregar dados. Verifique sua conexão.');
    } finally {
      // Only unset loading if this was the last request (controller matches)
      // Actually, if canceled, we returned early, so this finally block runs still?
      // Yes, finally runs on return. But we don't want to setLoading(false) if we just started a NEW one.
      // But since we use a global variable on window (hacky but works for this scope) or ref...
      // Let's rely on the fact that if it wasn't canceled, it's the latest.
      if (!controller.signal.aborted) {
        setLoading(false);
      }
      // Note: "window.abortController" requires type augmentation.
      // A better React way is a useRef, but fetchData is defined inside the component so it has access to refs.
    }
  }, [activeTab, minScore, user, premiumFilters]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const showNotification = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 3000);
  };

  // Download Weekly Report PDF (Premium Only)
  const downloadReport = async () => {
    if (!user?.is_premium) {
      showNotification('error', '🔒 Relatório semanal é um recurso Premium');
      router.push('/pricing');
      return;
    }

    try {
      showNotification('success', 'Gerando relatório...');
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/reports/weekly`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'relatorio_semanal.pdf');
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      showNotification('success', 'Relatório baixado com sucesso!');
    } catch (error) {
      console.error('Error downloading report:', error);
      showNotification('error', 'Erro ao baixar relatório');
    }
  };

  const filteredStocks = stocks.filter(s => {
    const matchesSearch = s.papel.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.setor?.toLowerCase().includes(searchTerm.toLowerCase());

    // Quick proxy for Blue Chip vs Small Cap based on Price (Cotacao) or Liquidity if available
    // Ideally use 'liquidez_corrente' but let's check if it exists or use price as fallback for MVP demo
    // Blue Chip: Price > 20 (Mock) OR Liquidity > 10M
    // Small Cap: Price < 20 (Mock) OR Liquidity < 5M
    let matchesFilter = true;

    // Use price as simple proxy if liquidity is missing/0
    const price = s.cotacao || 0;

    if (onlyBlueChips) {
      matchesFilter = price > 30; // Mock threshold for "Big"
    }
    if (onlySmallCaps) {
      matchesFilter = price < 30; // Mock threshold for "Small"
    }

    // Logic: if both selected, they might cancel out or show nothing, so let's enforce radio behavior via UI, 
    // but here we just check sequentially

    return matchesSearch && matchesFilter;
  });


  // Kill List: Removed History, Strategies, and Onboarding for simplified MVP

  const tabs = [
    { id: 'overview', label: 'Ranking (Fundamentus)', icon: Zap },
    { id: 'fusion', label: 'Ação Perfeita', icon: Target },
    { id: 'monitor', label: 'Monitor', icon: Shield },
    { id: 'anti-ranking', label: 'Ações Tóxicas', icon: Skull },
  ];

  // Show loading while checking auth

  // Show loading while checking auth
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-950">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-8 h-8 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full"
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen relative">
      {/* Animated Background */}
      <div className="bg-mesh" />


      {/* Notification - Using Portal to bypass parent transforms */}
      {typeof document !== 'undefined' && createPortal(
        <AnimatePresence>
          {notification && (
            <motion.div
              initial={{ opacity: 0, y: -50 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -50 }}
              style={{
                position: 'fixed',
                top: '1rem',
                left: '50%',
                transform: 'translateX(-50%)',
                zIndex: 99999
              }}
              className={`px-6 py-3 rounded-xl flex items-center gap-3 backdrop-blur-md ${notification.type === 'success'
                ? 'bg-green-500/20 border border-green-500/50 text-green-400'
                : 'bg-red-500/20 border border-red-500/50 text-red-400'
                }`}
            >
              {notification.type === 'success' ? <Zap className="w-5 h-5" /> : <X className="w-5 h-5" />}
              {notification.message}
            </motion.div>
          )}
        </AnimatePresence>,
        document.body
      )}

      {/* Content */}
      <div className="relative z-10">
        {/* Header */}
        <header className="dashboard-header">
          <div className="dashboard-header-inner">
            <div className="dashboard-header-content">
              <motion.div
                className="dashboard-logo"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
              >
                <div className="dashboard-logo-icon">
                  <Sparkles style={{ width: '1.5rem', height: '1.5rem', color: 'white' }} />
                </div>
                <div className="dashboard-logo-text">
                  <h1 className="gradient-text">NorteAcoes</h1>
                  <p>Análise Fundamentalista</p>
                </div>
              </motion.div>

              <div className="dashboard-actions">
                {/* Search */}
                <div className="dashboard-search">
                  <Search className="dashboard-search-icon" />
                  <input
                    type="text"
                    placeholder="Buscar ações ou setores..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="dashboard-search-input"
                  />
                </div>

                <motion.button
                  onClick={fetchData}
                  className="dashboard-btn-icon"
                  disabled={loading}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <RefreshCw style={{ width: '1.25rem', height: '1.25rem' }} className={loading ? 'animate-spin' : ''} />
                </motion.button>

                {/* Download Report Button */}
                <motion.button
                  onClick={downloadReport}
                  className={`dashboard-btn-icon ${user?.is_premium ? 'text-purple-400 hover:text-purple-300' : 'text-gray-500'}`}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  title={user?.is_premium ? 'Baixar Relatório Semanal' : 'Relatório Premium'}
                >
                  <FileText style={{ width: '1.25rem', height: '1.25rem' }} />
                </motion.button>

                {/* User Menu */}
                {user && (
                  <div className="dashboard-user">
                    <div className="dashboard-user-info">
                      <div className="dashboard-user-avatar">
                        <User style={{ width: '1rem', height: '1rem', color: 'white' }} />
                      </div>
                      <span className="dashboard-user-name">{user.name}</span>
                    </div>
                    <motion.button
                      onClick={logout}
                      className="dashboard-btn-icon dashboard-btn-logout"
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      title="Sair"
                    >
                      <LogOut style={{ width: '1.25rem', height: '1.25rem' }} />
                    </motion.button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        <div className="dashboard-main pt-8">
          {/* Enriched Stats Sections */}
          <div className="space-y-8 mb-8">
            {/* Row 1: Market Intelligence */}
            <section>
              <div className="flex items-center gap-2 mb-4 px-1">
                <div className="w-1 h-6 bg-cyan-500 rounded-full" />
                <h2 className="text-sm font-bold text-white/70 uppercase tracking-wider flex items-center gap-2">
                  <BarChart3 className="w-4 h-4" /> Inteligência de Mercado
                </h2>
              </div>
              <div className="dashboard-stats-grid">
                <StatCard
                  title="Total de Ações"
                  value={stats?.total_stocks || 0}
                  icon={BarChart3}
                  gradient="from-cyan-400 to-blue-600"
                  change={filteredStocks.length}
                  changeLabel="filtradas"
                />
                <StatCard
                  title="Oportunidades"
                  value={stats?.opportunities_count || 0}
                  subtitle="Score > 80"
                  icon={Zap}
                  gradient="from-yellow-400 to-orange-600"
                  tooltip="Ações com Super Score acima de 80, indicando forte potencial fundamentalista."
                />
                <StatCard
                  title="Top Ação"
                  value={stats?.top_stock || 'N/A'}
                  subtitle={`Fusion: ${stats?.top_score || 0}`}
                  icon={Trophy}
                  gradient="from-green-400 to-emerald-600"
                  isHighlighted={true}
                  tooltip="Melhor relação Risco/Retorno baseada no Algoritmo Fusion (Preço x Qualidade)."
                />
                <StatCard
                  title="Sentimento"
                  value={stats?.market_sentiment || 'Neutro'}
                  icon={Sparkles}
                  gradient={stats?.market_sentiment?.includes('Bull') || stats?.market_sentiment?.includes('Alta') ? "from-emerald-400 to-teal-600" : stats?.market_sentiment?.includes('Bear') || stats?.market_sentiment?.includes('Baixa') ? "from-red-400 to-rose-600" : "from-slate-400 to-slate-600"}
                  valueColor={stats?.market_sentiment?.includes('Bull') || stats?.market_sentiment?.includes('Alta') ? "text-emerald-400" : stats?.market_sentiment?.includes('Bear') || stats?.market_sentiment?.includes('Baixa') ? "text-red-400" : "text-slate-400"}
                  tooltip="Sentimento geral do mercado baseado em indicadores técnicos e volume."
                />
              </div>
            </section>

            {/* Row 2: Performance & Quality */}
            <section>
              <div className="flex items-center gap-2 mb-4 px-1">
                <div className="w-1 h-6 bg-purple-500 rounded-full" />
                <h2 className="text-sm font-bold text-white/70 uppercase tracking-wider flex items-center gap-2">
                  <Activity className="w-4 h-4" /> Performance & Qualidade
                </h2>
              </div>
              <div className="dashboard-stats-grid">
                <StatCard
                  title="Ações Tóxicas"
                  value={stats?.toxic_count || 0}
                  subtitle="Score Baixo"
                  icon={Skull}
                  gradient="from-red-400 to-rose-600"
                  valueColor="text-red-400"
                  tooltip="Ações com péssimos fundamentos econômicos ou risco iminente de insolvência."
                />
                <StatCard
                  title="Score Médio"
                  value={stats?.avg_super_score?.toFixed(1) || '0'}
                  icon={Zap}
                  gradient="from-purple-400 to-pink-600"
                />
                <StatCard
                  title="Setores Ativos"
                  value={stats?.sectors_count || 0}
                  icon={PieChart}
                  gradient="from-orange-400 to-red-600"
                />
                <StatCard
                  title="ROE Médio (Top 10)"
                  value={`${stats?.avg_roe || 0}%`}
                  icon={Activity}
                  gradient="from-indigo-400 to-blue-600"
                  tooltip="Return on Equity: Eficiência da empresa em gerar lucro sobre o patrimônio."
                />
              </div>
            </section>

            {/* Row 3: Efficiency & Growth */}
            <section>
              <div className="flex items-center gap-2 mb-4 px-1">
                <div className="w-1 h-6 bg-amber-500 rounded-full" />
                <h2 className="text-sm font-bold text-white/70 uppercase tracking-wider flex items-center gap-2">
                  <Calculator className="w-4 h-4" /> Eficiência & Valuation
                </h2>
              </div>
              <div className="dashboard-stats-grid">
                <StatCard
                  title="DY Médio (Top 10)"
                  value={`${stats?.avg_dividend_yield || 0}%`}
                  icon={Target}
                  gradient="from-emerald-400 to-teal-600"
                  tooltip="Dividend Yield: Percentual de proventos pagos em relação ao preço da ação."
                />
                <StatCard
                  title="P/L Médio (Top 10)"
                  value={stats?.avg_pl || 0}
                  icon={Calculator}
                  gradient="from-slate-400 to-gray-600"
                  tooltip="Preço sobre Lucro: Indica quanto o mercado paga por cada real de lucro."
                />
                <StatCard
                  title="Setor Líder"
                  value={stats?.best_sector || 'N/A'}
                  subtitle="Mais presente no Top 50"
                  icon={Briefcase}
                  gradient="from-cyan-400 to-blue-600"
                  tooltip="Setor com maior número de empresas de alta qualidade no momento."
                />
                <StatCard
                  title="Crescimento (5a)"
                  value={`${stats?.avg_growth || 0}%`}
                  icon={TrendingUp}
                  gradient="from-cyan-400 to-emerald-600"
                />
              </div>
            </section>
          </div>

          {/* Tabs */}
          <div className="dashboard-nav">
            {tabs.map((tab) => (
              <motion.button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`dashboard-nav-btn ${activeTab === tab.id ? 'active' : ''}`}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <tab.icon style={{ width: '1.25rem', height: '1.25rem' }} />
                {tab.label}
              </motion.button>
            ))}
          </div>

          {/* Tab Content */}
          <AnimatePresence mode="wait">
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                {/* Unified Premium Banner for Free Users */}
                {user && !user.is_premium && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-6 p-4 rounded-xl bg-gradient-to-r from-yellow-500/10 via-orange-500/10 to-yellow-500/10 border border-yellow-500/20"
                  >
                    <div className="flex items-center justify-between flex-wrap gap-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-yellow-500/20 flex items-center justify-center">
                          <Lock className="w-5 h-5 text-yellow-400" />
                        </div>
                        <div>
                          <p className="font-bold text-white">
                            Acesso Limitado - {displayedStocks.length} de {totalStocksCount}+ ações
                          </p>
                          <p className="text-sm text-white/60">
                            Desbloqueie Top 3, scores completos e filtros avançados
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() => router.push('/pricing')}
                        className="px-5 py-2.5 bg-gradient-to-r from-yellow-400 to-orange-500 text-black font-bold rounded-lg text-sm hover:scale-105 transition-transform shadow-lg shadow-yellow-500/20"
                      >
                        Assinar Agora
                      </button>
                    </div>
                  </motion.div>
                )}

                {/* Filters - Compact */}
                <PremiumFilters
                  isPremium={user?.is_premium || false}
                  sectors={sectors}
                  onFiltersChange={setPremiumFilters}
                  onUpgradeClick={() => router.push('/pricing')}
                />

                {/* Stock Cards Grid */}
                <div className="mb-8">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-bold text-white">
                      {user?.is_premium ? 'Todas as Ações' : 'Amostra do Ranking'}
                    </h2>
                    <span className="text-sm text-white/50">{displayedStocks.length} ações</span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {displayedStocks.map((stock, index) => (
                      <StockCard
                        key={stock.papel}
                        stock={stock}
                        index={index}
                        isPremium={user?.is_premium || false}
                        onClick={setSelectedStock}
                        isSelected={!!battleStocks.find(s => s.papel === stock.papel)}
                        onToggleSelect={toggleBattleSelection}
                      />
                    ))}
                  </div>

                  {/* Simple message below cards for free users */}
                  {user && !user.is_premium && displayedStocks.length > 0 && (
                    <div className="mt-6 text-center">
                      <p className="text-white/40 text-sm">
                        Mostrando {displayedStocks.length} ações do ranking •
                        <span
                          className="text-yellow-400 hover:underline cursor-pointer ml-1"
                          onClick={() => router.push('/pricing')}
                        >
                          Ver todas as {totalStocksCount}+ ações →
                        </span>
                      </p>
                    </div>
                  )}

                  {displayedStocks.length === 0 && (
                    <div className="text-center py-12 text-white/40">
                      Nenhuma ação encontrada com os filtros atuais.
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {/* Fusion Tab */}
            {activeTab === 'fusion' && (
              <motion.div
                key="fusion"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="mt-4"
              >
                <FusionTab />
              </motion.div>
            )}

            {/* Monitor Tab */}
            {activeTab === 'monitor' && (
              <motion.div
                key="monitor"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="mt-4"
              >
                <MonitorTab />
              </motion.div>
            )}

            {/* Anti-Ranking Tab - Toxic Stocks */}
            {activeTab === 'anti-ranking' && (
              <motion.div
                key="anti-ranking"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                <ToxicStocks
                  stocks={stocks
                    .filter(s =>
                      (s.super_score !== undefined && s.super_score < 10) ||
                      (s.p_l !== undefined && s.p_l < 0) ||
                      (s.roe !== undefined && s.roe < 0) ||
                      (s.div_bruta_patrimonio !== undefined && s.div_bruta_patrimonio > 2)
                    )
                    .sort((a, b) => (a.super_score || 0) - (b.super_score || 0))
                  }
                  isPremium={user?.is_premium || false}
                  onSelectStock={setSelectedStock}
                />
              </motion.div>
            )}


          </AnimatePresence>
        </div >
      </div >


      {selectedStock && typeof document !== 'undefined' && createPortal(
        <PremiumStockModal ticker={selectedStock.papel} isOpen={true} onClose={() => setSelectedStock(null)} />,
        document.body
      )
      }
      {
        notification && typeof document !== 'undefined' && createPortal(
          <div
            style={{
              position: 'fixed',
              bottom: '2rem',
              right: '2rem',
              padding: '1rem 1.5rem',
              borderRadius: '0.75rem',
              backgroundColor: notification.type === 'success' ? 'rgba(34, 197, 94, 0.95)' : 'rgba(239, 68, 68, 0.95)',
              color: 'white',
              fontWeight: 500,
              boxShadow: '0 10px 40px rgba(0, 0, 0, 0.3)',
              zIndex: 99999,
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              animation: 'slideInUp 0.3s ease-out'
            }}
          >
            {notification.type === 'success' ? (
              <Sparkles style={{ width: '1.25rem', height: '1.25rem' }} />
            ) : (
              <X style={{ width: '1.25rem', height: '1.25rem' }} />
            )}
            {notification.message}
          </div>,
          document.body
        )
      }

      {/* AI Chat Floating Button */}
      <AIChat />

      {/* Suggested Portfolio Floating Button */}
      <SuggestedPortfolio />

      {/* Floating Battle Button */}
      {
        battleStocks.length > 0 && (
          <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 flex items-center gap-4 bg-slate-900/90 backdrop-blur-md p-2 pl-6 pr-2 rounded-full border border-yellow-500/30 shadow-2xl shadow-yellow-500/10 animate-in slide-in-from-bottom-10 fade-in duration-300">
            <div className="flex -space-x-2">
              {battleStocks.map(s => (
                <div key={s.papel} className="w-8 h-8 rounded-full bg-slate-800 border-2 border-slate-900 flex items-center justify-center text-[10px] font-bold text-white">
                  {s.papel.substring(0, 4)}
                </div>
              ))}
              {battleStocks.length < 2 && (
                <div className="w-8 h-8 rounded-full bg-slate-800/50 border-2 border-slate-900 border-dashed flex items-center justify-center text-[10px] text-white/20">
                  ?
                </div>
              )}
            </div>

            <div className="text-xs text-white/50">
              <strong className="text-white">{battleStocks.length}</strong>/2 Selecionadas
            </div>

            <button
              disabled={battleStocks.length < 2}
              onClick={() => setShowBattleModal(true)}
              className={`px-4 py-2 rounded-full font-bold text-xs flex items-center gap-2 transition-all ${battleStocks.length === 2 ? 'bg-yellow-400 text-slate-900 hover:scale-105 shadow-lg shadow-yellow-400/20' : 'bg-white/10 text-white/30 cursor-not-allowed'}`}
            >
              <Zap className="w-3 h-3 fill-current" />
              BATALHAR
            </button>

            {battleStocks.length > 0 && (
              <button
                onClick={() => setBattleStocks([])}
                className="w-8 h-8 rounded-full hover:bg-white/10 flex items-center justify-center text-white/30 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        )
      }

      {
        showBattleModal && battleStocks.length === 2 && (
          <StockComparisonModal
            stockA={battleStocks[0]}
            stockB={battleStocks[1]}
            onClose={() => setShowBattleModal(false)}
          />
        )
      }

    </div >
  );
}

// ============================================
// COMPONENTS
// ============================================

// StatCard has been moved to ./components/StatCard.tsx




