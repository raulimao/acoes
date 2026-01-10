'use client';

import { AuthProvider } from './contexts/AuthContext';
import { DataCacheProvider } from './contexts/DataCacheContext';

export function Providers({ children }: { children: React.ReactNode }) {
    return (
        <DataCacheProvider>
            <AuthProvider>
                {children}
            </AuthProvider>
        </DataCacheProvider>
    );
}
