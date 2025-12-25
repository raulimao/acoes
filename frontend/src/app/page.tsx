'use client';

import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import {
  ChevronUp,
  ChevronDown,
  Search,
  RefreshCw,
  Sparkles,
  Trophy,
  Zap,
  Info,
  X,
  LogOut,
  User,
  BarChart3,
  PieChart,
  Target,
  Skull
} from 'lucide-react';
import AIChat from './components/AIChat';
import SuggestedPortfolio from './components/SuggestedPortfolio';
import EngagementWidgets from './components/EngagementWidgets';
import StockComparisonModal from '../components/StockComparisonModal';
import StockCard from '../components/StockCard';
import { useAuth } from './contexts/AuthContext';
import { useRouter } from 'next/navigation';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

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
}

interface Stats {
  total_stocks: number;
  avg_super_score: number;
  top_stock: string;
  top_score: number;
  sectors_count: number;
}

export default function Dashboard() {
  const router = useRouter();
  const { user, isAuthenticated, loading: authLoading, logout } = useAuth();
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [searchTerm, setSearchTerm] = useState('');
  const [minScore, setMinScore] = useState(5);
  // Filters
  const [onlyBlueChips, setOnlyBlueChips] = useState(false);
  const [onlySmallCaps, setOnlySmallCaps] = useState(false);

  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);
  const [notification, setNotification] = useState<{ type: 'success' | 'error', message: string } | null>(null);

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

  useEffect(() => {
    fetchData();
  }, [minScore, activeTab]); // Re-fetch when tab changes (to handle sorting logic if needed from API)

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  // Debug: Log when selectedStock changes
  useEffect(() => {
    console.log('selectedStock state changed:', selectedStock?.papel || 'null');
  }, [selectedStock]);

  const fetchData = async () => {
    setLoading(true);
    try {
      // For Anti-Ranking, we want distinct logic: maybe 0 to 5 score
      // For Overview, we use minScore
      const isAntiRanking = activeTab === 'anti-ranking';

      let endpoint = `${API_URL}/stocks?limit=50`;

      if (isAntiRanking) {
        // Fetch worst stocks: max_score=15 (min in db is ~9), sort_by=super_score, order=asc
        endpoint += `&max_score=15&sort_by=super_score&order=asc`;
      } else {
        // Normal fetching
        endpoint += `&min_score=${minScore}`;
      }

      const [stocksRes, statsRes] = await Promise.all([
        axios.get(endpoint),
        axios.get(`${API_URL}/stats`)
      ]);
      setStocks(stocksRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      showNotification('error', 'Erro ao carregar dados da API');
    } finally {
      setLoading(false);
    }
  };

  const showNotification = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 3000);
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

  const getScoreColor = (score: number) => {
    if (score >= 12) return 'score-high';
    if (score >= 8) return 'score-medium';
    return 'score-low';
  };

  const getScoreTextColor = (score: number) => {
    if (score >= 12) return 'text-green-400';
    if (score >= 8) return 'text-yellow-400';
    return 'text-red-400';
  };

  // Kill List: Removed History, Strategies, and Onboarding for simplified MVP

  const tabs = [
    { id: 'overview', label: 'Ranking Geral', icon: Zap }, // Renamed from "Visão Geral" to "Ranking Geral" for clarity
    { id: 'ranking', label: 'Top 3', icon: Trophy },
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
                  <h1 className="gradient-text">TopAções</h1>
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

                {/* Refresh */}
                <motion.button
                  onClick={fetchData}
                  className="dashboard-btn-icon"
                  disabled={loading}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <RefreshCw style={{ width: '1.25rem', height: '1.25rem' }} className={loading ? 'animate-spin' : ''} />
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

        <div className="dashboard-main">
          {/* Stats Cards */}
          <motion.div
            className="dashboard-stats-grid"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <StatCard
              title="Total de Ações"
              value={stats?.total_stocks || 0}
              icon={BarChart3}
              gradient="from-cyan-400 to-blue-600"
              change={filteredStocks.length}
              changeLabel="filtradas"
            />
            <StatCard
              title="Score Médio"
              value={stats?.avg_super_score?.toFixed(1) || '0'}
              icon={PieChart}
              gradient="from-purple-400 to-pink-600"
            />
            <StatCard
              title="Top Ação"
              value={stats?.top_stock || 'N/A'}
              subtitle={`Score: ${stats?.top_score || 0}`}
              icon={Trophy}
              gradient="from-green-400 to-emerald-600"
            />
            <StatCard
              title="Setores"
              value={stats?.sectors_count || 0}
              icon={Target}
              gradient="from-orange-400 to-red-600"
            />
          </motion.div>

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
            {(activeTab === 'overview' || activeTab === 'anti-ranking') && (
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                {/* Engagement Widgets (Alerts & Reports) */}
                {activeTab === 'overview' && <EngagementWidgets />}

                {/* Score Filter & Toggles - Only show on Overview */}
                {activeTab === 'overview' && (
                  <div className="card mb-8">
                    <div className="flex items-center justify-between flex-wrap gap-4">
                      <div>
                        <h3 className="text-lg font-semibold mb-1">Filtros Inteligentes</h3>
                        <p className="text-white/50 text-sm">
                          Mínimo Super Score: <span className="text-cyan-400 font-bold text-lg">{minScore}</span>
                        </p>
                      </div>

                      <div className="flex items-center gap-6">
                        {/* Range Slider */}
                        <div className="flex items-center gap-4">
                          <span className="text-white/40">0</span>
                          <input
                            type="range"
                            min="0"
                            max="20"
                            step="0.5"
                            value={minScore}
                            onChange={(e) => setMinScore(Number(e.target.value))}
                            className="w-64 accent-cyan-400 h-2 bg-white/10 rounded-lg appearance-none cursor-pointer"
                          />
                          <span className="text-white/40">20</span>
                        </div>

                        {/* Toggles */}
                        <div className="h-8 w-px bg-white/10 mx-2" />

                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => { setOnlyBlueChips(!onlyBlueChips); setOnlySmallCaps(false); }}
                            className={`px-4 py-2 rounded-lg text-sm font-bold border transition-colors ${onlyBlueChips ? 'bg-blue-600 border-blue-500 text-white' : 'bg-white/5 border-white/10 text-white/40 hover:text-white'}`}
                          >
                            💎 Blue Chips
                          </button>
                          <button
                            onClick={() => { setOnlySmallCaps(!onlySmallCaps); setOnlyBlueChips(false); }}
                            className={`px-4 py-2 rounded-lg text-sm font-bold border transition-colors ${onlySmallCaps ? 'bg-purple-600 border-purple-500 text-white' : 'bg-white/5 border-white/10 text-white/40 hover:text-white'}`}
                          >
                            🚀 Small Caps
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'anti-ranking' && (
                  <div className="mb-8 p-6 rounded-2xl bg-gradient-to-r from-red-900/40 to-orange-900/40 border border-red-500/20">
                    <div className="flex items-center gap-4 mb-2">
                      <Skull className="w-8 h-8 text-red-500" />
                      <h2 className="text-2xl font-bold text-white">Zona de Perigo: Ações Tóxicas</h2>
                    </div>
                    <p className="text-white/60">
                      Estas ações possuem os piores indicadores fundamentais. <span className="text-red-400 font-bold">Cuidado redobrado</span> ao investir nestes ativos.
                    </p>
                  </div>
                )}



                {/* Stock Cards Grid (Replaces Table) */}
                <div className="mb-8">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold">
                      {activeTab === 'anti-ranking' ? 'Ranking Reverso (Piores Scores)' : 'Top Ações por Super Score'}
                    </h2>
                    <span className="text-white/50">{filteredStocks.length} resultados</span>
                  </div>

                  {user && !user.is_premium && (
                    <div className="mb-6 p-4 rounded-xl bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border border-yellow-500/20 text-yellow-200 text-sm flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-yellow-400" />
                        <span>Você está vendo apenas a Top 1 gratuita. Assine o Pro para ver o ranking completo.</span>
                      </div>
                      <button className="px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-black font-bold rounded-lg text-xs transition-colors">
                        Assinar Agora
                      </button>
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredStocks.map((stock, index) => (
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

                  {filteredStocks.length === 0 && (
                    <div className="text-center py-12 text-white/40">
                      Nenhuma ação encontrada com os filtros atuais.
                    </div>
                  )}
                </div>
              </motion.div>
            )}



            {/* Ranking Tab */}
            {activeTab === 'ranking' && (
              <motion.div
                key="ranking"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                  {/* Top 3 Podium */}
                  {stocks.slice(0, 3).map((stock, index) => (
                    <motion.div
                      key={stock.papel}
                      className={`card relative overflow-hidden ${index === 0 ? 'lg:order-2 border-2 border-yellow-500/50' :
                        index === 1 ? 'lg:order-1 border-2 border-gray-400/50' :
                          'lg:order-3 border-2 border-orange-600/50'
                        }`}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: index * 0.15 }}
                    >
                      <div className={`absolute top-0 left-0 right-0 h-1 ${index === 0 ? 'bg-gradient-to-r from-yellow-400 to-yellow-600' :
                        index === 1 ? 'bg-gradient-to-r from-gray-300 to-gray-500' :
                          'bg-gradient-to-r from-orange-400 to-orange-600'
                        }`} />

                      <div className="text-center py-4">
                        <div className={`w-16 h-16 mx-auto rounded-full flex items-center justify-center text-2xl font-bold mb-4 ${index === 0 ? 'bg-gradient-to-br from-yellow-400 to-yellow-600' :
                          index === 1 ? 'bg-gradient-to-br from-gray-300 to-gray-500' :
                            'bg-gradient-to-br from-orange-400 to-orange-600'
                          }`}>
                          {index + 1}°
                        </div>

                        <h3 className="text-2xl font-bold gradient-text mb-2">{stock.papel}</h3>
                        <p className="text-white/50 mb-4">{stock.setor || 'Sem setor'}</p>

                        <div className="stat-value text-4xl mb-2">
                          {stock.super_score?.toFixed(1)}
                        </div>
                        <p className="text-white/40 text-sm">Super Score</p>

                        <div className="grid grid-cols-2 gap-4 mt-6 text-sm">
                          <div className="bg-white/5 rounded-lg p-3">
                            <p className="text-white/40">P/L</p>
                            <p className="font-bold">{stock.p_l?.toFixed(2)}</p>
                          </div>
                          <div className="bg-white/5 rounded-lg p-3">
                            <p className="text-white/40">DY</p>
                            <p className="font-bold">{stock.dividend_yield?.toFixed(2)}%</p>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>

                {/* Full ranking table */}
                <div className="card">
                  <h3 className="text-xl font-bold mb-6">Ranking Completo</h3>
                  <StockTable stocks={filteredStocks} onSelect={setSelectedStock} showRank />
                </div>
              </motion.div>
            )}


          </AnimatePresence>
        </div>
      </div>

      {selectedStock && typeof document !== 'undefined' && createPortal(
        <StockModal stock={selectedStock} onClose={() => setSelectedStock(null)} />,
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
      {battleStocks.length > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-4 bg-slate-900/90 backdrop-blur-md p-2 pl-6 pr-2 rounded-full border border-yellow-500/30 shadow-2xl shadow-yellow-500/10 animate-in slide-in-from-bottom-10 fade-in duration-300">
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
      )}

      {showBattleModal && battleStocks.length === 2 && (
        <StockComparisonModal
          stockA={battleStocks[0]}
          stockB={battleStocks[1]}
          onClose={() => setShowBattleModal(false)}
        />
      )}

    </div >
  );
}

// ============================================
// COMPONENTS
// ============================================

function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  gradient,
  change,
  changeLabel
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ElementType;
  gradient: string;
  change?: number;
  changeLabel?: string;
}) {
  return (
    <motion.div
      className="card card-glow relative overflow-hidden group"
      whileHover={{ scale: 1.02 }}
      transition={{ type: 'spring', stiffness: 300 }}
    >
      <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-0 group-hover:opacity-5 transition-opacity`} />

      <div className="flex items-start justify-between">
        <div>
          <p className="text-white/50 text-sm mb-2">{title}</p>
          <p className="stat-value gradient-text">{value}</p>
          {subtitle && <p className="text-white/40 text-sm mt-1">{subtitle}</p>}
          {change !== undefined && (
            <p className="text-cyan-400 text-sm mt-1">{change} {changeLabel}</p>
          )}
        </div>
        <div className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${gradient} flex items-center justify-center opacity-80`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </motion.div>
  );
}

function StockTable({ stocks, onSelect, showRank = false }: { stocks: Stock[], onSelect: (s: Stock) => void, showRank?: boolean }) {
  const getScoreColor = (score: number) => {
    if (score >= 12) return 'score-high';
    if (score >= 8) return 'score-medium';
    return 'score-low';
  };

  return (
    <div className="dashboard-table-container">
      <table className="dashboard-table">
        <thead>
          <tr>
            {showRank && <th>#</th>}
            <th>Ação</th>
            <th>Setor</th>
            <th>Cotação</th>
            <th>P/L</th>
            <th>P/VP</th>
            <th>DY</th>
            <th>ROE</th>
            <th>Super Score</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {stocks.map((stock, index) => (
            <motion.tr
              key={stock.papel}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.02 }}
              className="hover:bg-cyan-500/5 cursor-pointer transition-colors"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Row clicked, selecting stock:', stock.papel);
                onSelect(stock);
              }}
            >
              {showRank && (
                <td>
                  <span className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${index < 3 ? 'bg-gradient-to-r from-yellow-500 to-orange-500' : 'bg-white/10'
                    }`}>
                    {index + 1}
                  </span>
                </td>
              )}
              <td className="font-bold text-white">{stock.papel}</td>
              <td className="text-white/60">{stock.setor || 'N/A'}</td>
              <td>R$ {stock.cotacao?.toFixed(2) || '0.00'}</td>
              <td>{stock.p_l?.toFixed(2) || '0'}</td>
              <td>{stock.p_vp?.toFixed(2) || '0'}</td>
              <td>{stock.dividend_yield?.toFixed(2) || '0'}%</td>
              <td>{stock.roe?.toFixed(2) || '0'}%</td>
              <td>
                <span className={`score-badge ${getScoreColor(stock.super_score || 0)}`}>
                  <Zap className="w-4 h-4 mr-1" />
                  {stock.super_score?.toFixed(1) || '0'}
                </span>
              </td>
              <td>
                <Info className="w-5 h-5 text-white/30 hover:text-cyan-400 transition-colors" />
              </td>
            </motion.tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function StockModal({ stock, onClose }: { stock: Stock, onClose: () => void }) {
  const getScoreColor = (score: number) => {
    if (score >= 12) return 'text-green-400';
    if (score >= 8) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/80 backdrop-blur-md z-[200] flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.9, y: 20 }}
        className="card max-w-lg w-full"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold gradient-text">{stock.papel}</h2>
            <p className="text-white/50">{stock.setor || 'Sem setor'}</p>
          </div>
          <button
            onClick={onClose}
            className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-white/5 rounded-xl p-4">
            <p className="text-white/40 text-sm mb-1">Cotação</p>
            <p className="text-xl font-bold">R$ {stock.cotacao?.toFixed(2)}</p>
          </div>
          <div className="bg-white/5 rounded-xl p-4">
            <p className="text-white/40 text-sm mb-1">Super Score</p>
            <p className={`text-xl font-bold ${getScoreColor(stock.super_score || 0)}`}>
              {stock.super_score?.toFixed(2)}
            </p>
          </div>
        </div>

        <div className="space-y-3">
          <h3 className="font-semibold mb-2">Indicadores</h3>
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-white/5 rounded-lg p-3 text-center">
              <p className="text-white/40 text-xs">P/L</p>
              <p className="font-bold">{stock.p_l?.toFixed(2)}</p>
            </div>
            <div className="bg-white/5 rounded-lg p-3 text-center">
              <p className="text-white/40 text-xs">P/VP</p>
              <p className="font-bold">{stock.p_vp?.toFixed(2)}</p>
            </div>
            <div className="bg-white/5 rounded-lg p-3 text-center">
              <p className="text-white/40 text-xs">DY</p>
              <p className="font-bold">{stock.dividend_yield?.toFixed(2)}%</p>
            </div>
            <div className="bg-white/5 rounded-lg p-3 text-center">
              <p className="text-white/40 text-xs">ROE</p>
              <p className="font-bold">{stock.roe?.toFixed(2)}%</p>
            </div>
            <div className="bg-white/5 rounded-lg p-3 text-center">
              <p className="text-white/40 text-xs">ROIC</p>
              <p className="font-bold">{stock.roic?.toFixed(2)}%</p>
            </div>
            <div className="bg-white/5 rounded-lg p-3 text-center">
              <p className="text-white/40 text-xs">Liq. Corr.</p>
              <p className="font-bold">{stock.liquidez_corrente?.toFixed(2)}</p>
            </div>
          </div>
        </div>

        <div className="mt-6 pt-6 border-t border-white/10">
          <h3 className="font-semibold mb-3">Scores por Estratégia</h3>
          <div className="grid grid-cols-4 gap-2">
            <div className="text-center">
              <p className="text-xs text-white/40">Graham</p>
              <p className={`font-bold ${getScoreColor(stock.score_graham || 0)}`}>
                {stock.score_graham?.toFixed(1)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-xs text-white/40">Greenblatt</p>
              <p className={`font-bold ${getScoreColor(stock.score_greenblatt || 0)}`}>
                {stock.score_greenblatt?.toFixed(1)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-xs text-white/40">Bazin</p>
              <p className={`font-bold ${getScoreColor(stock.score_bazin || 0)}`}>
                {stock.score_bazin?.toFixed(1)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-xs text-white/40">Qualidade</p>
              <p className={`font-bold ${getScoreColor(stock.score_qualidade || 0)}`}>
                {stock.score_qualidade?.toFixed(1)}
              </p>
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
