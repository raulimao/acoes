'use client';

import { motion } from 'framer-motion';
import { XCircle, ArrowLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function PaymentCancelPage() {
    const router = useRouter();

    return (
        <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-gray-800 p-8 rounded-2xl shadow-2xl max-w-md w-full text-center border border-red-500/30"
            >
                <div className="flex justify-center mb-6">
                    <XCircle className="w-24 h-24 text-red-500" />
                </div>

                <h1 className="text-3xl font-bold text-white mb-4">Pagamento Cancelado</h1>
                <p className="text-gray-400 mb-8">
                    O processo de pagamento não foi concluído. Nenhuma cobrança foi feita.
                </p>

                <div className="space-y-3">
                    <button
                        onClick={() => router.push('/pricing')}
                        className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 rounded-xl transition-colors"
                    >
                        Tentar Novamente
                    </button>

                    <button
                        onClick={() => router.push('/')}
                        className="w-full bg-transparent border border-gray-600 hover:bg-gray-700 text-gray-300 font-bold py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
                    >
                        <ArrowLeft className="w-5 h-5" /> Voltar ao Dashboard
                    </button>
                </div>
            </motion.div>
        </div>
    );
}
