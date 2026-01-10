'use client';

import React, { createContext, useContext, useState, useCallback, useRef } from 'react';

interface CacheEntry {
    data: any;
    timestamp: number;
}

interface DataCacheContextType {
    getCachedData: (key: string) => any | null;
    setCachedData: (key: string, data: any) => void;
    invalidateCache: (key?: string) => void;
}

const DataCacheContext = createContext<DataCacheContextType | undefined>(undefined);

const STALE_TIME = 5 * 60 * 1000; // 5 minutes

export const DataCacheProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    // Using a ref for the cache object to avoid unnecessary re-renders of the provider
    // unless the provider itself is remounted. Consumers will only re-render if they
    // explicitly call getCachedData during their render cycle or in a useEffect.
    const cache = useRef<{ [key: string]: CacheEntry }>({});

    const getCachedData = useCallback((key: string) => {
        const entry = cache.current[key];
        if (!entry) return null;

        const isStale = Date.now() - entry.timestamp > STALE_TIME;
        if (isStale) {
            delete cache.current[key];
            return null;
        }

        return entry.data;
    }, []);

    const setCachedData = useCallback((key: string, data: any) => {
        cache.current[key] = {
            data,
            timestamp: Date.now(),
        };
    }, []);

    const invalidateCache = useCallback((key?: string) => {
        if (key) {
            delete cache.current[key];
        } else {
            cache.current = {};
        }
    }, []);

    return (
        <DataCacheContext.Provider value={{ getCachedData, setCachedData, invalidateCache }}>
            {children}
        </DataCacheContext.Provider>
    );
};

export const useDataCache = () => {
    const context = useContext(DataCacheContext);
    if (context === undefined) {
        throw new Error('useDataCache must be used within a DataCacheProvider');
    }
    return context;
};
