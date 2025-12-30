'use client';

import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

export function LoadingSkeleton() {
    return (
        <div className="min-h-screen p-6 space-y-6">
            {/* Header Skeleton */}
            <div className="flex justify-between items-center">
                <div className="space-y-2">
                    <SkeletonBlock width="200px" height="32px" />
                    <SkeletonBlock width="300px" height="16px" />
                </div>
                <SkeletonBlock width="120px" height="40px" rounded="xl" />
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {[...Array(4)].map((_, i) => (
                    <SkeletonCard key={i} />
                ))}
            </div>

            {/* Tabs */}
            <div className="flex gap-2">
                {[...Array(4)].map((_, i) => (
                    <SkeletonBlock key={i} width="100px" height="40px" rounded="xl" />
                ))}
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <SkeletonChartCard />
                <SkeletonChartCard />
            </div>

            {/* Table */}
            <SkeletonTable />
        </div>
    );
}

function SkeletonBlock({
    width,
    height,
    rounded = 'lg'
}: {
    width: string;
    height: string;
    rounded?: string;
}) {
    return (
        <motion.div
            initial={{ opacity: 0.5 }}
            animate={{ opacity: [0.5, 0.8, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            style={{
                width,
                height,
                borderRadius: rounded === 'xl' ? '0.75rem' : '0.5rem',
                background: 'linear-gradient(90deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.1) 50%, rgba(255,255,255,0.05) 100%)',
                backgroundSize: '200% 100%'
            }}
            className="shimmer"
        />
    );
}

function SkeletonCard() {
    return (
        <div
            style={{
                padding: '1.5rem',
                borderRadius: '1rem',
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(255,255,255,0.05)'
            }}
        >
            <div className="flex justify-between items-start mb-4">
                <SkeletonBlock width="60%" height="16px" />
                <SkeletonBlock width="40px" height="40px" rounded="xl" />
            </div>
            <SkeletonBlock width="80%" height="32px" />
            <div className="mt-3">
                <SkeletonBlock width="50%" height="14px" />
            </div>
        </div>
    );
}

function SkeletonChartCard() {
    return (
        <div
            style={{
                padding: '1.5rem',
                borderRadius: '1rem',
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(255,255,255,0.05)'
            }}
        >
            <SkeletonBlock width="40%" height="20px" />
            <div className="mt-6 flex items-end gap-2" style={{ height: '200px' }}>
                {[...Array(8)].map((_, i) => (
                    <motion.div
                        key={i}
                        initial={{ opacity: 0.5 }}
                        animate={{ opacity: [0.5, 0.8, 0.5] }}
                        transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.1 }}
                        style={{
                            flex: 1,
                            height: `${((i * 37) % 60) + 40}%`, // Deterministic random-like value based on index
                            borderRadius: '0.5rem 0.5rem 0 0',
                            background: 'linear-gradient(180deg, rgba(139, 92, 246, 0.3) 0%, rgba(139, 92, 246, 0.1) 100%)'
                        }}
                    />
                ))}
            </div>
        </div>
    );
}

function SkeletonTable() {
    return (
        <div
            style={{
                padding: '1.5rem',
                borderRadius: '1rem',
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(255,255,255,0.05)'
            }}
        >
            <div className="flex justify-between mb-6">
                <SkeletonBlock width="30%" height="20px" />
                <SkeletonBlock width="200px" height="36px" rounded="xl" />
            </div>

            {/* Table Header */}
            <div className="grid grid-cols-6 gap-4 mb-4 pb-4" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                {[...Array(6)].map((_, i) => (
                    <SkeletonBlock key={i} width="80%" height="14px" />
                ))}
            </div>

            {/* Table Rows */}
            {[...Array(5)].map((_, rowIdx) => (
                <motion.div
                    key={rowIdx}
                    initial={{ opacity: 0.5 }}
                    animate={{ opacity: [0.5, 0.8, 0.5] }}
                    transition={{ duration: 1.5, repeat: Infinity, delay: rowIdx * 0.1 }}
                    className="grid grid-cols-6 gap-4 py-4"
                    style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}
                >
                    {[...Array(6)].map((_, colIdx) => (
                        <SkeletonBlock
                            key={colIdx}
                            width={colIdx === 0 ? '60px' : '70%'}
                            height="20px"
                        />
                    ))}
                </motion.div>
            ))}
        </div>
    );
}

export default LoadingSkeleton;
