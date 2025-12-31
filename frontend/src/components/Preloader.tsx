'use client';
import { useEffect } from 'react';
import ReactDOM from 'react-dom';

export default function Preloader() {
    useEffect(() => {
        // Inicia o handshake TLS imediatamente ao carregar o JS
        ReactDOM.preconnect('https://acoes.onrender.com', { crossOrigin: 'anonymous' });
        ReactDOM.prefetchDNS('https://acoes.onrender.com');
    }, []);
    return null;
}
