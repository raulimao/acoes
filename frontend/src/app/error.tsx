'use client';

import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        // Log error to an error reporting service if needed
        console.error(error);
    }, [error]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
            <div className="bg-mesh opacity-20" />

            <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="relative z-10 max-w-md w-full bg-slate-900/80 backdrop-blur-xl border border-white/10 p-8 rounded-2xl shadow-2xl text-center"
            >
                <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
                    <AlertTriangle className="w-8 h-8 text-red-500" />
                </div>

                <h2 className="text-2xl font-bold text-white mb-2">Algo deu errado!</h2>
                <p className="text-slate-400 mb-8">
                    Encontramos um erro inesperado. Nossa equipe já foi notificada.
                </p>

                <button
                    onClick={() => reset()}
                    className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-6 rounded-xl transition-all flex items-center justify-center gap-2"
                >
                    <RefreshCw className="w-5 h-5" />
                    Tentar Novamente
                </button>
            </motion.div>
        </div>
    );
}
