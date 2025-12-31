import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  compiler: {
    removeConsole: process.env.NODE_ENV === "production",
  },
  experimental: {
    scrollRestoration: true,
  },
  transpilePackages: ['lucide-react', 'recharts', 'framer-motion', 'react-day-picker'],
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Link',
            value: '<https://acoes.onrender.com>; rel=preconnect; crossorigin=anonymous',
          },
        ],
      },
    ];
  },
};

export default nextConfig;
