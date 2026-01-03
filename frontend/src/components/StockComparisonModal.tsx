import { motion } from 'framer-motion';
import { X, Trophy, AlertTriangle, Check, Zap } from 'lucide-react';

interface Stock {
    papel: string;
    setor?: string;
    cotacao?: number;
    p_l?: number;
    p_vp?: number;
    dividend_yield?: number;
    roe?: number;
    roic?: number;
    margem_liquida?: number;
    liquidez_corrente?: number;
    div_bruta_patrimonio?: number;
    super_score?: number;
    score_graham?: number;
    score_greenblatt?: number;
    score_bazin?: number;
    score_qualidade?: number;
}

interface StockComparisonModalProps {
    stockA: Stock;
    stockB: Stock;
    onClose: () => void;
}

export default function StockComparisonModal({ stockA, stockB, onClose }: StockComparisonModalProps) {

    // Helper to determine winner for a metric
    // higherIsBetter: true for DY, ROE, Score. False for P/L, P/VP, Endividamento.
    const getWinner = (valA: number | undefined, valB: number | undefined, higherIsBetter: boolean = true) => {
        if (valA === undefined || valB === undefined || valA === null || valB === null) return null;
        if (valA === valB) return 'tie';
        if (higherIsBetter) return valA > valB ? 'A' : 'B';
        return valA < valB ? 'A' : 'B';
    };

    const metrics = [
        // Scores
        { label: 'Super Score', key: 'super_score', higherIsBetter: true, format: (v: number) => v?.toFixed(1) ?? 'N/A' },
        { label: 'Score Graham', key: 'score_graham', higherIsBetter: true, format: (v: number) => v?.toFixed(1) ?? 'N/A' },
        { label: 'Score Greenblatt', key: 'score_greenblatt', higherIsBetter: true, format: (v: number) => v?.toFixed(1) ?? 'N/A' },
        { label: 'Score Bazin', key: 'score_bazin', higherIsBetter: true, format: (v: number) => v?.toFixed(1) ?? 'N/A' },
        { label: 'Score Qualidade', key: 'score_qualidade', higherIsBetter: true, format: (v: number) => v?.toFixed(1) ?? 'N/A' },

        // Valuation
        { label: 'Cotação', key: 'cotacao', higherIsBetter: false, format: (v: number) => v ? `R$ ${v.toFixed(2)}` : 'N/A' },
        { label: 'P/L', key: 'p_l', higherIsBetter: false, format: (v: number) => v?.toFixed(2) ?? 'N/A' },
        { label: 'P/VP', key: 'p_vp', higherIsBetter: false, format: (v: number) => v?.toFixed(2) ?? 'N/A' },

        // Dividendos & Rentabilidade
        { label: 'Dividend Yield', key: 'dividend_yield', higherIsBetter: true, format: (v: number) => v ? `${(v * 100).toFixed(2)}%` : 'N/A' },
        { label: 'ROE', key: 'roe', higherIsBetter: true, format: (v: number) => v ? `${(v * 100).toFixed(2)}%` : 'N/A' },
        { label: 'ROIC', key: 'roic', higherIsBetter: true, format: (v: number) => v ? `${(v * 100).toFixed(2)}%` : 'N/A' },
        { label: 'Margem Líquida', key: 'margem_liquida', higherIsBetter: true, format: (v: number) => v ? `${(v * 100).toFixed(2)}%` : 'N/A' },

        // Saúde Financeira
        { label: 'Liquidez Corrente', key: 'liquidez_corrente', higherIsBetter: true, format: (v: number) => v?.toFixed(2) ?? 'N/A' },
        { label: 'Dív.Bruta/Patrim.', key: 'div_bruta_patrimonio', higherIsBetter: false, format: (v: number) => v?.toFixed(2) ?? 'N/A' },
    ];

    // Calculate overall winner
    let winsA = 0;
    let winsB = 0;

    metrics.forEach(m => {
        const winner = getWinner(stockA[m.key as keyof Stock] as number, stockB[m.key as keyof Stock] as number, m.higherIsBetter);
        if (winner === 'A') winsA++;
        if (winner === 'B') winsB++;
    });

    const overallWinner = winsA > winsB ? 'A' : winsB > winsA ? 'B' : 'Tie';

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/90 backdrop-blur-md z-[200] flex items-center justify-center p-4 overflow-y-auto"
            onClick={onClose}
        >
            <motion.div
                initial={{ scale: 0.9, y: 20 }}
                animate={{ scale: 1, y: 0 }}
                exit={{ scale: 0.9, y: 20 }}
                className="bg-slate-900 border border-white/10 rounded-2xl w-full max-w-4xl p-6 relative shadow-2xl shadow-purple-500/20"
                onClick={(e) => e.stopPropagation()}
            >
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 w-10 h-10 rounded-full bg-white/5 flex items-center justify-center hover:bg-white/10 transition-colors z-10"
                >
                    <X className="w-5 h-5 text-white/50" />
                </button>

                <div className="text-center mb-8">
                    <h2 className="text-3xl font-bold gradient-text flex items-center justify-center gap-3">
                        <Zap className="w-8 h-8 text-yellow-400" />
                        Batalha de Ações
                        <Zap className="w-8 h-8 text-yellow-400" />
                    </h2>
                    <p className="text-white/40">Comparativo lado a lado</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {/* Stock A Header */}
                    <div className={`text-center p-4 rounded-xl border transition-colors ${overallWinner === 'A' ? 'bg-gradient-to-b from-green-500/20 to-transparent border-green-500/50' : 'bg-white/5 border-white/5'}`}>
                        <h3 className="text-2xl font-bold text-white mb-2">{stockA.papel}</h3>
                        <p className="text-white/50 text-sm mb-4">{stockA.setor}</p>
                        {overallWinner === 'A' && (
                            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/20 text-green-400 text-sm font-bold border border-green-500/30">
                                <Trophy className="w-4 h-4" /> VENCEDORA
                            </div>
                        )}
                        <div className="mt-4 text-3xl font-bold gradient-text">
                            {stockA.super_score?.toFixed(1)}
                            <span className="text-sm text-white/30 block font-normal">Super Score</span>
                        </div>
                    </div>

                    {/* VS */}
                    <div className="flex items-center justify-center flex-col">
                        <span className="text-4xl font-black text-white/10 italic">VS</span>
                    </div>

                    {/* Stock B Header */}
                    <div className={`text-center p-4 rounded-xl border transition-colors ${overallWinner === 'B' ? 'bg-gradient-to-b from-green-500/20 to-transparent border-green-500/50' : 'bg-white/5 border-white/5'}`}>
                        <h3 className="text-2xl font-bold text-white mb-2">{stockB.papel}</h3>
                        <p className="text-white/50 text-sm mb-4">{stockB.setor}</p>
                        {overallWinner === 'B' && (
                            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/20 text-green-400 text-sm font-bold border border-green-500/30">
                                <Trophy className="w-4 h-4" /> VENCEDORA
                            </div>
                        )}
                        <div className="mt-4 text-3xl font-bold gradient-text">
                            {stockB.super_score?.toFixed(1)}
                            <span className="text-sm text-white/30 block font-normal">Super Score</span>
                        </div>
                    </div>
                </div>

                {/* Comparison Table */}
                <div className="mt-8 space-y-2">
                    {metrics.map((metric) => {
                        const valA = stockA[metric.key as keyof Stock] as number;
                        const valB = stockB[metric.key as keyof Stock] as number;
                        const winner = getWinner(valA, valB, metric.higherIsBetter);

                        // Special formatting for % if needed, but for now assuming direct numbers or pre-formatted
                        // Actually my 'format' function in metrics map handles it.
                        // Re-verify 'format' logic for DY/ROE based on API response.
                        // Assuming API returns straight numbers like 3.98 for 3.98%.

                        const formattedA = metric.format ? metric.format(valA || 0) : valA;
                        const formattedB = metric.format ? metric.format(valB || 0) : valB;

                        return (
                            <div key={metric.key} className="grid grid-cols-3 gap-2 md:gap-6 py-3 border-b border-white/5 hover:bg-white/5 transition-colors px-2 md:px-4 rounded-lg">
                                <div className={`text-right font-mono font-bold ${winner === 'A' ? 'text-green-400 scale-110 origin-right' : 'text-white/60'}`}>
                                    {formattedA}
                                </div>
                                <div className="text-center text-white/40 text-sm flex items-center justify-center gap-2 uppercase tracking-wider">
                                    {metric.label}
                                </div>
                                <div className={`text-left font-mono font-bold ${winner === 'B' ? 'text-green-400 scale-110 origin-left' : 'text-white/60'}`}>
                                    {formattedB}
                                </div>
                            </div>
                        );
                    })}
                </div>

                <div className="mt-8 text-center">
                    <p className="text-white/30 text-sm">
                        * A análise automatizada considera apenas indicadores quantitativos.
                    </p>
                </div>

            </motion.div>
        </motion.div>
    );
}
