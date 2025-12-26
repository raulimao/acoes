'use client';

import { motion } from 'framer-motion';
import { CheckCircle, ArrowRight } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import confetti from 'canvas-confetti';

export default function PaymentSuccessPage() {
    const router = useRouter();

    useEffect(() => {
        // Trigger confetti
        confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 }
        });

        // Redirect after 5 seconds
        const timeout = setTimeout(() => {
            router.push('/');
        }, 5000);

        return () => clearTimeout(timeout);
    }, [router]);

    return (
        <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-gray-800 p-8 rounded-2xl shadow-2xl max-w-md w-full text-center border border-green-500/30"
            >
                <div className="flex justify-center mb-6">
                    <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: "spring", stiffness: 200, damping: 10 }}
                    >
                        <CheckCircle className="w-24 h-24 text-green-500" />
                    </motion.div>
                </div>

                <h1 className="text-3xl font-bold text-white mb-4">Pagamento Confirmado!</h1>
                <p className="text-gray-400 mb-8">
                    Parabéns! Você agora é um assinante <strong>Premium</strong>.
                    Todos os recursos foram desbloqueados.
                </p>

                <button
                    onClick={() => router.push('/')}
                    className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 rounded-xl flex items-center justify-center gap-2 transition-colors"
                >
                    Ir para o Dashboard <ArrowRight className="w-5 h-5" />
                </button>
            </motion.div>
        </div>
    );
}
