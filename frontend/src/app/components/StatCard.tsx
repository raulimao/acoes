'use client';

import React from 'react';
import { motion } from 'framer-motion';

export interface StatCardProps {
    title: string;
    value: string | number;
    subtitle?: string;
    icon: React.ElementType;
    gradient: string;
    change?: number;
    changeLabel?: string;
    isHighlighted?: boolean;
    valueColor?: string;
    tooltip?: string;
}

export default function StatCard({
    title,
    value,
    subtitle,
    icon: Icon,
    gradient,
    change,
    changeLabel,
    isHighlighted,
    valueColor,
    tooltip
}: StatCardProps) {
    return (
        <motion.div
            className={`card card-glow relative overflow-hidden group h-full flex flex-col justify-between cursor-default transition-all duration-300 ${isHighlighted ? 'stat-card-highlight' : ''}`}
            whileHover={{ scale: 1.02, translateY: -4 }}
            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
        >
            <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-0 group-hover:opacity-5 transition-opacity`} />

            <div className="flex flex-col h-full">
                <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-1.5" title={tooltip}>
                        <p className="text-white/40 text-[11px] font-bold uppercase tracking-wider">{title}</p>
                        {tooltip && (
                            <div className="w-3.5 h-3.5 rounded-full border border-white/20 flex items-center justify-center text-[9px] text-white/30 cursor-help hover:border-white/40 hover:text-white/60 transition-colors">
                                ?
                            </div>
                        )}
                    </div>
                    <div className={`flex items-center justify-center`}>
                        <Icon className={`w-5 h-5 opacity-90 transition-transform group-hover:scale-110 duration-500`} style={{ color: gradient.includes('from-') ? undefined : 'white' }} />
                    </div>
                </div>

                <div className="mt-auto">
                    <p className={`${valueColor || 'gradient-text'} stat-value block truncate`} title={String(value)}>
                        {value}
                    </p>
                    <div className="flex items-center justify-between mt-1 min-h-[20px]">
                        {subtitle && <p className="card-subtitle truncate max-w-full" title={subtitle}>{subtitle}</p>}
                        {change !== undefined && (
                            <p className="text-cyan-400 text-[10px] font-bold uppercase tracking-tight">{change} {changeLabel}</p>
                        )}
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
