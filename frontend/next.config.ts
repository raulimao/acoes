import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  compiler: {
    removeConsole: process.env.NODE_ENV === "production",
  },
  experimental: {
    optimizeCss: {
      pruneSource: false,
      inlineFonts: false,
    },
    optimizePackageImports: ['lucide-react', 'recharts', 'framer-motion'],
    scrollRestoration: true,
  },
  transpilePackages: ['lucide-react', 'recharts', 'framer-motion', 'react-day-picker'],
};

export default nextConfig;
