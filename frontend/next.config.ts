import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: [
    'lucide-react',
    'recharts',
    'framer-motion',
    'clsx',
    'tailwind-merge'
  ],
  experimental: {
    optimizeCss: true,
    scrollRestoration: true,
  },
};

export default nextConfig;
