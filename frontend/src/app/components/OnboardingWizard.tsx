'use client';
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface OnboardingWizardProps {
    onComplete: (profile: string) => void;
}

const QUESTIONS = [
    {
        id: 'objective',
        question: 'Qual seu principal objetivo ao investir?',
        options: [
            { value: 'income', label: '💰 Renda passiva (dividendos)', points: { conservador: 3, moderado: 1, agressivo: 0 } },
            { value: 'growth', label: '📈 Valorização do patrimônio', points: { conservador: 0, moderado: 2, agressivo: 3 } },
            { value: 'both', label: '⚖️ Um pouco de cada', points: { conservador: 1, moderado: 3, agressivo: 1 } }
        ]
    },
    {
        id: 'horizon',
        question: 'Por quanto tempo pretende manter seus investimentos?',
        options: [
            { value: 'short', label: '⚡ Menos de 2 anos', points: { conservador: 0, moderado: 1, agressivo: 3 } },
            { value: 'medium', label: '📅 2 a 5 anos', points: { conservador: 1, moderado: 3, agressivo: 2 } },
            { value: 'long', label: '🏔️ Mais de 5 anos', points: { conservador: 3, moderado: 2, agressivo: 1 } }
        ]
    },
    {
        id: 'risk',
        question: 'Como você reagiria se sua carteira caísse 30%?',
        options: [
            { value: 'sell', label: '😰 Venderia tudo para evitar mais perdas', points: { conservador: 3, moderado: 0, agressivo: 0 } },
            { value: 'wait', label: '😐 Manteria e esperaria recuperar', points: { conservador: 1, moderado: 3, agressivo: 1 } },
            { value: 'buy', label: '🤑 Compraria mais aproveitando a queda', points: { conservador: 0, moderado: 1, agressivo: 3 } }
        ]
    }
];

const PROFILES = {
    conservador: {
        name: 'Conservador',
        icon: '🛡️',
        color: '#3b82f6',
        description: 'Você prioriza segurança e renda passiva. Foco em empresas sólidas com bons dividendos.'
    },
    moderado: {
        name: 'Moderado',
        icon: '⚖️',
        color: '#10b981',
        description: 'Você busca equilíbrio entre crescimento e segurança. Mix de dividendos e valorização.'
    },
    agressivo: {
        name: 'Agressivo',
        icon: '🚀',
        color: '#f59e0b',
        description: 'Você busca máximo retorno e aceita riscos. Foco em crescimento e alta rentabilidade.'
    }
};

export default function OnboardingWizard({ onComplete }: OnboardingWizardProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [currentStep, setCurrentStep] = useState(0);
    const [answers, setAnswers] = useState<{ [key: string]: string }>({});
    const [result, setResult] = useState<string | null>(null);

    // Check if user already completed onboarding
    useEffect(() => {
        const savedProfile = localStorage.getItem('investorProfile');
        const hasSeenOnboarding = localStorage.getItem('hasSeenOnboarding');

        if (!savedProfile && !hasSeenOnboarding) {
            // Show onboarding after 2 seconds
            const timer = setTimeout(() => setIsOpen(true), 2000);
            return () => clearTimeout(timer);
        }
    }, []);

    const handleAnswer = (questionId: string, value: string) => {
        setAnswers(prev => ({ ...prev, [questionId]: value }));

        if (currentStep < QUESTIONS.length - 1) {
            setTimeout(() => setCurrentStep(prev => prev + 1), 300);
        } else {
            // Calculate result
            const scores = { conservador: 0, moderado: 0, agressivo: 0 };

            QUESTIONS.forEach(q => {
                const answer = { ...answers, [questionId]: value }[q.id];
                const option = q.options.find(o => o.value === answer);
                if (option) {
                    scores.conservador += option.points.conservador;
                    scores.moderado += option.points.moderado;
                    scores.agressivo += option.points.agressivo;
                }
            });

            const profile = Object.entries(scores).sort((a, b) => b[1] - a[1])[0][0];
            setResult(profile);
            localStorage.setItem('investorProfile', profile);
            localStorage.setItem('hasSeenOnboarding', 'true');
        }
    };

    const handleComplete = () => {
        if (result) {
            onComplete(result);
        }
        setIsOpen(false);
    };

    const handleSkip = () => {
        localStorage.setItem('hasSeenOnboarding', 'true');
        setIsOpen(false);
    };

    if (!isOpen) return null;

    const currentQuestion = QUESTIONS[currentStep];
    const profileData = result ? PROFILES[result as keyof typeof PROFILES] : null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                style={{
                    position: 'fixed',
                    inset: 0,
                    background: 'rgba(0, 0, 0, 0.85)',
                    backdropFilter: 'blur(8px)',
                    zIndex: 100,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '1rem'
                }}
            >
                <motion.div
                    initial={{ scale: 0.9, y: 20 }}
                    animate={{ scale: 1, y: 0 }}
                    style={{
                        background: 'linear-gradient(180deg, #1f2937 0%, #111827 100%)',
                        borderRadius: '1.5rem',
                        maxWidth: '500px',
                        width: '100%',
                        overflow: 'hidden',
                        border: '1px solid rgba(255,255,255,0.1)',
                        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
                    }}
                >
                    {!result ? (
                        <>
                            {/* Header */}
                            <div style={{
                                background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                                padding: '2rem',
                                textAlign: 'center'
                            }}>
                                <span style={{ fontSize: '3rem' }}>👋</span>
                                <h2 style={{ color: 'white', margin: '0.5rem 0 0', fontSize: '1.5rem', fontWeight: 700 }}>
                                    Bem-vindo ao TopAções!
                                </h2>
                                <p style={{ color: 'rgba(255,255,255,0.8)', margin: '0.5rem 0 0' }}>
                                    Responda 3 perguntas rápidas para personalizar suas recomendações
                                </p>
                            </div>

                            {/* Progress */}
                            <div style={{ padding: '1rem 2rem 0' }}>
                                <div style={{ display: 'flex', gap: '0.5rem' }}>
                                    {QUESTIONS.map((_, i) => (
                                        <div key={i} style={{
                                            flex: 1,
                                            height: '4px',
                                            borderRadius: '2px',
                                            background: i <= currentStep ? '#10b981' : 'rgba(255,255,255,0.1)'
                                        }} />
                                    ))}
                                </div>
                                <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.8rem', margin: '0.5rem 0 0' }}>
                                    Pergunta {currentStep + 1} de {QUESTIONS.length}
                                </p>
                            </div>

                            {/* Question */}
                            <div style={{ padding: '1.5rem 2rem' }}>
                                <AnimatePresence mode="wait">
                                    <motion.div
                                        key={currentStep}
                                        initial={{ opacity: 0, x: 20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: -20 }}
                                    >
                                        <h3 style={{ color: 'white', margin: '0 0 1.5rem', fontSize: '1.1rem' }}>
                                            {currentQuestion.question}
                                        </h3>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                            {currentQuestion.options.map(option => (
                                                <motion.button
                                                    key={option.value}
                                                    whileHover={{ scale: 1.02 }}
                                                    whileTap={{ scale: 0.98 }}
                                                    onClick={() => handleAnswer(currentQuestion.id, option.value)}
                                                    style={{
                                                        padding: '1rem 1.25rem',
                                                        borderRadius: '0.75rem',
                                                        border: '1px solid rgba(255,255,255,0.1)',
                                                        background: 'rgba(255,255,255,0.05)',
                                                        color: 'white',
                                                        textAlign: 'left',
                                                        cursor: 'pointer',
                                                        fontSize: '1rem'
                                                    }}
                                                >
                                                    {option.label}
                                                </motion.button>
                                            ))}
                                        </div>
                                    </motion.div>
                                </AnimatePresence>
                            </div>

                            {/* Skip */}
                            <div style={{ padding: '0 2rem 1.5rem', textAlign: 'center' }}>
                                <button
                                    onClick={handleSkip}
                                    style={{
                                        background: 'none',
                                        border: 'none',
                                        color: 'rgba(255,255,255,0.4)',
                                        cursor: 'pointer',
                                        fontSize: '0.85rem'
                                    }}
                                >
                                    Pular por agora
                                </button>
                            </div>
                        </>
                    ) : (
                        /* Result */
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            style={{ padding: '2rem', textAlign: 'center' }}
                        >
                            <motion.div
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                transition={{ type: 'spring', delay: 0.2 }}
                                style={{
                                    width: '100px',
                                    height: '100px',
                                    borderRadius: '50%',
                                    background: `linear-gradient(135deg, ${profileData?.color}40, ${profileData?.color}20)`,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    margin: '0 auto 1.5rem',
                                    fontSize: '3rem',
                                    border: `2px solid ${profileData?.color}`
                                }}
                            >
                                {profileData?.icon}
                            </motion.div>

                            <h2 style={{ color: 'white', margin: '0 0 0.5rem', fontSize: '1.5rem' }}>
                                Seu perfil é <span style={{ color: profileData?.color }}>{profileData?.name}</span>!
                            </h2>

                            <p style={{ color: 'rgba(255,255,255,0.7)', margin: '0 0 2rem', lineHeight: 1.6 }}>
                                {profileData?.description}
                            </p>

                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={handleComplete}
                                style={{
                                    background: `linear-gradient(135deg, ${profileData?.color}, ${profileData?.color}dd)`,
                                    border: 'none',
                                    borderRadius: '0.75rem',
                                    padding: '1rem 2rem',
                                    color: 'white',
                                    fontWeight: 600,
                                    cursor: 'pointer',
                                    fontSize: '1rem'
                                }}
                            >
                                Ver minha carteira sugerida →
                            </motion.button>
                        </motion.div>
                    )}
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
}
