'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, X, Send, Sparkles, Bot, User, Loader2 } from 'lucide-react';
import axios from 'axios';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

const QUICK_SUGGESTIONS = [
    "Quais são as 5 melhores ações?",
    "Explique a estratégia Graham",
    "Ações com P/L < 10",
    "Ações do setor bancário",
    "Quem mais evoluiu esse mês?",
];

export default function AIChat() {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<Message[]>([
        {
            role: 'assistant',
            content: '👋 Olá! Sou o Analista IA do NorteAcoes.\n\nPosso ajudar você com:\n• Análise de ações específicas\n• Comparar ativos\n• Explicar estratégias (Graham, Greenblatt, Bazin)\n• Buscar por critérios (P/L, DY, ROE)\n• Ver evolução histórica\n\nO que você gostaria de saber?',
            timestamp: new Date()
        }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [showSuggestions, setShowSuggestions] = useState(true);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const sendMessage = async (e?: React.FormEvent, messageText?: string) => {
        if (e) e.preventDefault();
        const textToSend = messageText || input;
        if (!textToSend.trim() || loading) return;

        const userMessage: Message = {
            role: 'user',
            content: textToSend,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setLoading(true);
        setShowSuggestions(false); // Hide suggestions after first message

        try {
            const token = localStorage.getItem('token');
            const response = await axios.post(`${API_URL}/chat`, {
                message: textToSend,
                history: messages.slice(-6).map(m => ({ role: m.role, content: m.content }))
            }, {
                headers: { Authorization: `Bearer ${token}` }
            });

            const assistantMessage: Message = {
                role: 'assistant',
                content: response.data.response,
                timestamp: new Date()
            };

            setMessages(prev => [...prev, assistantMessage]);
        } catch {
            // Fallback response if API fails
            const fallbackMessage: Message = {
                role: 'assistant',
                content: 'Desculpe, não consegui processar sua mensagem. Por favor, tente novamente em instantes.',
                timestamp: new Date()
            };
            setMessages(prev => [...prev, fallbackMessage]);
        } finally {
            setLoading(false);
        }
    };

    const sendSuggestion = (suggestion: string) => {
        sendMessage(undefined, suggestion);
    };

    return (
        <>
            {/* Floating Chat Button */}
            <AnimatePresence>
                {!isOpen && (
                    <motion.button
                        initial={{ scale: 0, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0, opacity: 0 }}
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={() => setIsOpen(true)}
                        style={{
                            position: 'fixed',
                            bottom: '2rem',
                            right: '2rem',
                            width: '4rem',
                            height: '4rem',
                            borderRadius: '50%',
                            background: 'linear-gradient(135deg, #8b5cf6, #06b6d4)',
                            border: 'none',
                            boxShadow: '0 10px 40px rgba(139, 92, 246, 0.4)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            cursor: 'pointer',
                            zIndex: 50
                        }}
                    >
                        <MessageCircle className="w-7 h-7 text-white" />

                        {/* Pulse ring */}
                        <motion.div
                            animate={{ scale: [1, 1.4, 1], opacity: [0.5, 0, 0.5] }}
                            transition={{ duration: 2, repeat: Infinity }}
                            style={{
                                position: 'absolute',
                                inset: '-4px',
                                borderRadius: '50%',
                                border: '2px solid rgba(139, 92, 246, 0.5)'
                            }}
                        />
                    </motion.button>
                )}
            </AnimatePresence>

            {/* Chat Panel */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: 100, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 100, scale: 0.95 }}
                        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                        className="fixed bottom-24 right-6 w-96 max-w-[calc(100vw-2rem)] flex flex-col z-50"
                        style={{
                            maxHeight: 'calc(100vh - 4rem)',
                            background: 'rgba(15, 23, 42, 0.95)',
                            backdropFilter: 'blur(20px)',
                            border: '1px solid rgba(255, 255, 255, 0.1)',
                            borderRadius: '1.5rem',
                            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
                            overflow: 'hidden'
                        }}
                    >
                        {/* Header */}
                        <div
                            style={{
                                padding: '1rem 1.25rem',
                                borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                                background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(6, 182, 212, 0.1))',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between'
                            }}
                        >
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                <div
                                    style={{
                                        width: '2.5rem',
                                        height: '2.5rem',
                                        borderRadius: '0.75rem',
                                        background: 'linear-gradient(135deg, #8b5cf6, #06b6d4)',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center'
                                    }}
                                >
                                    <Sparkles className="w-5 h-5 text-white" />
                                </div>
                                <div>
                                    <h3 style={{ fontWeight: 600, fontSize: '0.95rem', color: 'white' }}>
                                        NorteAcoes AI
                                    </h3>
                                    <p style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)' }}>
                                        Powered by Groq
                                    </p>
                                </div>
                            </div>
                            <button
                                onClick={() => setIsOpen(false)}
                                style={{
                                    width: '2rem',
                                    height: '2rem',
                                    borderRadius: '0.5rem',
                                    background: 'rgba(255,255,255,0.05)',
                                    border: 'none',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    cursor: 'pointer',
                                    color: 'rgba(255,255,255,0.5)'
                                }}
                            >
                                <X className="w-4 h-4" />
                            </button>
                        </div>

                        {/* Messages */}
                        <div
                            style={{
                                flex: 1,
                                overflowY: 'auto',
                                padding: '1rem',
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '1rem'
                            }}
                        >
                            {messages.map((message, index) => (
                                <motion.div
                                    key={index}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    style={{
                                        display: 'flex',
                                        flexDirection: message.role === 'user' ? 'row-reverse' : 'row',
                                        gap: '0.5rem',
                                        alignItems: 'flex-start'
                                    }}
                                >
                                    <div
                                        style={{
                                            width: '1.75rem',
                                            height: '1.75rem',
                                            borderRadius: '0.5rem',
                                            background: message.role === 'user'
                                                ? 'linear-gradient(135deg, #22c55e, #10b981)'
                                                : 'linear-gradient(135deg, #8b5cf6, #06b6d4)',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            flexShrink: 0
                                        }}
                                    >
                                        {message.role === 'user'
                                            ? <User className="w-3.5 h-3.5 text-white" />
                                            : <Bot className="w-3.5 h-3.5 text-white" />
                                        }
                                    </div>
                                    <div
                                        style={{
                                            maxWidth: '80%',
                                            padding: '0.75rem 1rem',
                                            borderRadius: '1rem',
                                            background: message.role === 'user'
                                                ? 'rgba(34, 197, 94, 0.15)'
                                                : 'rgba(255, 255, 255, 0.05)',
                                            border: message.role === 'user'
                                                ? '1px solid rgba(34, 197, 94, 0.2)'
                                                : '1px solid rgba(255, 255, 255, 0.05)',
                                            color: 'rgba(255, 255, 255, 0.9)',
                                            fontSize: '0.875rem',
                                            lineHeight: 1.5
                                        }}
                                    >
                                        {message.content}
                                    </div>
                                </motion.div>
                            ))}

                            {/* Loading indicator */}
                            {loading && (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}
                                >
                                    <div
                                        style={{
                                            width: '1.75rem',
                                            height: '1.75rem',
                                            borderRadius: '0.5rem',
                                            background: 'linear-gradient(135deg, #8b5cf6, #06b6d4)',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center'
                                        }}
                                    >
                                        <Bot className="w-3.5 h-3.5 text-white" />
                                    </div>
                                    <div
                                        style={{
                                            padding: '0.75rem 1rem',
                                            borderRadius: '1rem',
                                            background: 'rgba(255, 255, 255, 0.05)',
                                            display: 'flex',
                                            gap: '0.25rem'
                                        }}
                                    >
                                        <motion.span
                                            animate={{ opacity: [0.3, 1, 0.3] }}
                                            transition={{ duration: 1, repeat: Infinity, delay: 0 }}
                                            style={{ width: '0.5rem', height: '0.5rem', borderRadius: '50%', background: 'white' }}
                                        />
                                        <motion.span
                                            animate={{ opacity: [0.3, 1, 0.3] }}
                                            transition={{ duration: 1, repeat: Infinity, delay: 0.2 }}
                                            style={{ width: '0.5rem', height: '0.5rem', borderRadius: '50%', background: 'white' }}
                                        />
                                        <motion.span
                                            animate={{ opacity: [0.3, 1, 0.3] }}
                                            transition={{ duration: 1, repeat: Infinity, delay: 0.4 }}
                                            style={{ width: '0.5rem', height: '0.5rem', borderRadius: '50%', background: 'white' }}
                                        />
                                    </div>
                                </motion.div>
                            )}

                            <div ref={messagesEndRef} />
                        </div>

                        {/* Quick Suggestions */}
                        {showSuggestions && messages.length <= 1 && (
                            <div
                                style={{
                                    padding: '0.5rem 1rem',
                                    borderTop: '1px solid rgba(255, 255, 255, 0.05)',
                                    display: 'flex',
                                    flexWrap: 'wrap',
                                    gap: '0.5rem'
                                }}
                            >
                                {QUICK_SUGGESTIONS.map((suggestion, index) => (
                                    <motion.button
                                        key={index}
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                        onClick={() => sendSuggestion(suggestion)}
                                        style={{
                                            padding: '0.375rem 0.75rem',
                                            borderRadius: '1rem',
                                            background: 'rgba(139, 92, 246, 0.1)',
                                            border: '1px solid rgba(139, 92, 246, 0.3)',
                                            color: 'rgba(255, 255, 255, 0.8)',
                                            fontSize: '0.75rem',
                                            cursor: 'pointer',
                                            whiteSpace: 'nowrap'
                                        }}
                                    >
                                        {suggestion}
                                    </motion.button>
                                ))}
                            </div>
                        )}

                        {/* Input */}
                        <form
                            onSubmit={sendMessage}
                            style={{
                                padding: '1rem',
                                borderTop: '1px solid rgba(255, 255, 255, 0.1)',
                                display: 'flex',
                                gap: '0.75rem'
                            }}
                        >
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Digite sua mensagem..."
                                autoFocus
                                disabled={loading}
                            />
                            <motion.button
                                type="submit"
                                disabled={loading || !input.trim()}
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                style={{
                                    width: '2.75rem',
                                    height: '2.75rem',
                                    borderRadius: '0.75rem',
                                    background: 'linear-gradient(135deg, #8b5cf6, #06b6d4)',
                                    border: 'none',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
                                    opacity: loading || !input.trim() ? 0.5 : 1
                                }}
                            >
                                {loading ? (
                                    <Loader2 className="w-5 h-5 text-white animate-spin" />
                                ) : (
                                    <Send className="w-5 h-5 text-white" />
                                )}
                            </motion.button>
                        </form>
                    </motion.div>
                )}
            </AnimatePresence >
        </>
    );
}
