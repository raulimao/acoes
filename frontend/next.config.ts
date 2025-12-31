import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  compiler: {
    removeConsole: process.env.NODE_ENV === "production",
  },
  experimental: {
    optimizeCss: true,
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
            value: '<https://acoes.onrender.com>; rel=preconnect; crossorigin; as=fetch',
          },
        ],
      },
    ];
  },
};

export default nextConfig;
